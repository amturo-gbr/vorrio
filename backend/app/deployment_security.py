from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from .config import AppConfig


UNSAFE_SECRET_KEYS = frozenset(
    {
        "development-change-me",
        "replace-with-at-least-32-random-characters",
    }
)


def is_safe_secret_key(secret_key: str) -> bool:
    return len(secret_key) >= 32 and secret_key not in UNSAFE_SECRET_KEYS


def _host_is_allowed(hostname: str, allowed_hosts: tuple[str, ...]) -> bool:
    host = hostname.rstrip(".").lower()
    for allowed in allowed_hosts:
        candidate = allowed.strip().rstrip(".").lower()
        if candidate == host:
            return True
        if candidate.startswith("*.") and host.endswith(candidate[1:]):
            return True
    return False


def public_exposure_failures(config: AppConfig) -> tuple[str, ...]:
    """Return stable reason codes for an unsafe direct-internet profile."""

    if config.deployment_profile != "public_https":
        return ()

    failures: list[str] = []
    if not config.public_exposure_acknowledged:
        failures.append("acknowledgement_missing")
    if not is_safe_secret_key(config.secret_key):
        failures.append("session_secret_unsafe")
    if not config.session_https_only:
        failures.append("secure_cookie_disabled")

    public = urlsplit(config.public_url) if config.public_url else None
    public_host = public.hostname if public else None
    if not public or public.scheme != "https" or not public_host:
        failures.append("canonical_https_url_missing")
    else:
        if not _host_is_allowed(public_host, config.trusted_hosts):
            failures.append("canonical_host_not_trusted")
        if config.public_url not in config.allowed_origins:
            failures.append("canonical_origin_not_allowed")

    if not config.trusted_hosts or "*" in config.trusted_hosts:
        failures.append("trusted_hosts_wildcard")
    proxies = {
        value.strip() for value in config.forwarded_allow_ips.split(",") if value.strip()
    }
    if not proxies or "*" in proxies:
        failures.append("forwarded_proxy_unrestricted")
    else:
        for proxy in proxies:
            if proxy.startswith("unix:"):
                continue
            try:
                network = ipaddress.ip_network(proxy, strict=False)
            except ValueError:
                failures.append("forwarded_proxy_invalid")
                break
            if network.prefixlen == 0:
                failures.append("forwarded_proxy_unrestricted")
                break
    if not config.allowed_origins:
        failures.append("allowed_origins_missing")

    return tuple(dict.fromkeys(failures))
