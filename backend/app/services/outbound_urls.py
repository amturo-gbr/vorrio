from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit


class OutboundUrlError(ValueError):
    pass


def normalize_connector_url(value: str, *, require_https: bool = False) -> str:
    """Validate an Owner-controlled Grocy or AI base URL.

    Private and loopback destinations remain supported deliberately for local
    self-hosting. Link-local, multicast, unspecified and reserved literal IPs
    are never valid connector targets.
    """

    raw = value.strip()
    if any(character.isspace() or ord(character) < 32 for character in raw):
        raise OutboundUrlError("Die Adresse enthält unzulässige Leer- oder Steuerzeichen")
    parsed = urlsplit(raw)
    allowed_schemes = {"https"} if require_https else {"http", "https"}
    if (
        parsed.scheme.lower() not in allowed_schemes
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        protocol = "HTTPS" if require_https else "HTTP(S)"
        raise OutboundUrlError(
            f"Die Adresse muss eine gültige {protocol}-Basis-URL ohne Zugangsdaten, Query oder Fragment sein"
        )
    try:
        parsed_port = parsed.port
    except ValueError as exc:
        raise OutboundUrlError("Die Adresse enthält einen ungültigen Port") from exc

    hostname = parsed.hostname.rstrip(".").lower()
    if not hostname or "%" in hostname or any(
        character.isspace() or ord(character) < 32 for character in hostname
    ):
        raise OutboundUrlError("Die Adresse enthält einen ungültigen Hostnamen")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and (
        address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or address.is_reserved
    ):
        raise OutboundUrlError("Link-lokale, reservierte oder Multicast-Ziele sind nicht erlaubt")

    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = rendered_host + (f":{parsed_port}" if parsed_port is not None else "")
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), netloc, path, "", ""))


def validate_public_push_url(value: str) -> str:
    """Validate the structural boundary of a browser-issued Web Push URL."""

    raw = value.strip()
    if any(character.isspace() or ord(character) < 32 for character in raw):
        raise OutboundUrlError("Der Push-Endpunkt enthält unzulässige Zeichen")
    parsed = urlsplit(raw)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise OutboundUrlError(
            "Der Push-Endpunkt muss eine gültige öffentliche HTTPS-URL sein"
        )
    hostname = parsed.hostname.rstrip(".").lower()
    try:
        parsed_port = parsed.port
    except ValueError as exc:
        raise OutboundUrlError("Der Push-Endpunkt enthält einen ungültigen Port") from exc
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise OutboundUrlError("Lokale Push-Endpunkte sind nicht erlaubt")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise OutboundUrlError("Private oder reservierte Push-Endpunkte sind nicht erlaubt")
    return raw


def validate_public_push_destination(value: str) -> str:
    """Resolve a push target and reject private or special-purpose addresses."""

    endpoint = validate_public_push_url(value)
    parsed = urlsplit(endpoint)
    hostname = str(parsed.hostname)
    try:
        addresses = {
            ipaddress.ip_address(result[4][0])
            for result in socket.getaddrinfo(
                hostname, parsed.port or 443, type=socket.SOCK_STREAM
            )
        }
    except (OSError, ValueError) as exc:
        raise OutboundUrlError("Der Push-Endpunkt kann nicht sicher aufgelöst werden") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise OutboundUrlError("Der Push-Endpunkt verweist auf ein nicht öffentliches Ziel")
    return endpoint
