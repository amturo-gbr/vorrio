from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_csv(value: str | None, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if value is None:
        return default
    parsed = tuple(part.strip() for part in value.split(",") if part.strip())
    return parsed or default


def _as_int(name: str, default: int, minimum: int, maximum: int) -> int:
    value = int(os.getenv(name, str(default)))
    return min(max(value, minimum), maximum)


def _origin(value: str) -> str:
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{value!r} ist keine gültige HTTP(S)-URL")
    try:
        parsed_port = parsed.port
    except ValueError as exc:
        raise ValueError(f"{value!r} enthält einen ungültigen Port") from exc
    host = parsed.hostname.lower()
    if "%" in host or any(
        character.isspace() or ord(character) < 32 for character in host
    ):
        raise ValueError(f"{value!r} enthält einen ungültigen Hostnamen")
    if ":" in host:
        host = f"[{host}]"
    port = f":{parsed_port}" if parsed_port is not None else ""
    return f"{parsed.scheme.lower()}://{host}{port}"


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    app_password: str
    secret_key: str
    deployment_profile: str
    public_url: str
    trusted_hosts: tuple[str, ...]
    allowed_origins: tuple[str, ...]
    forwarded_allow_ips: str
    session_https_only: bool
    public_exposure_acknowledged: bool
    max_upload_bytes: int
    max_request_bytes: int
    max_image_pixels: int
    receipt_retention_days: int
    login_max_failures: int
    login_window_seconds: int
    web_push_subject: str
    notification_check_seconds: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        data_dir = Path(os.getenv("DATA_DIR", "/data")).resolve()
        app_password = os.getenv("APP_PASSWORD", "")
        secret_key = os.getenv("APP_SECRET_KEY", "development-change-me")
        deployment_profile = os.getenv("DEPLOYMENT_PROFILE", "lan").strip().lower()
        if deployment_profile not in {"lan", "private_https", "public_https"}:
            raise ValueError(
                "DEPLOYMENT_PROFILE muss lan, private_https oder public_https sein"
            )
        public_url_value = os.getenv("PUBLIC_URL", "").strip()
        public_url = _origin(public_url_value) if public_url_value else ""
        allowed_origins = tuple(
            dict.fromkeys(
                _origin(value)
                for value in _as_csv(os.getenv("ALLOWED_ORIGINS"))
            )
        )
        max_upload_mb = _as_int("MAX_UPLOAD_MB", 12, 1, 100)
        max_request_mb = _as_int(
            "MAX_REQUEST_MB", max_upload_mb + 1, max_upload_mb, 110
        )
        web_push_subject = os.getenv(
            "WEB_PUSH_SUBJECT", "mailto:admin@vorrio.local"
        ).strip()
        if not web_push_subject.startswith(("mailto:", "https://")):
            raise ValueError("WEB_PUSH_SUBJECT muss mit mailto: oder https:// beginnen")
        return cls(
            data_dir=data_dir,
            app_password=app_password,
            secret_key=secret_key,
            deployment_profile=deployment_profile,
            public_url=public_url,
            trusted_hosts=_as_csv(os.getenv("TRUSTED_HOSTS"), ("*",)),
            allowed_origins=allowed_origins,
            forwarded_allow_ips=os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1").strip(),
            session_https_only=_as_bool(os.getenv("SESSION_HTTPS_ONLY")),
            public_exposure_acknowledged=_as_bool(
                os.getenv("PUBLIC_EXPOSURE_ACKNOWLEDGED")
            ),
            max_upload_bytes=max_upload_mb * 1024 * 1024,
            max_request_bytes=max_request_mb * 1024 * 1024,
            max_image_pixels=_as_int(
                "MAX_IMAGE_MEGAPIXELS", 40, 1, 200
            )
            * 1_000_000,
            receipt_retention_days=_as_int(
                "RECEIPT_RETENTION_DAYS", 7, 0, 365
            ),
            login_max_failures=_as_int("LOGIN_MAX_FAILURES", 5, 2, 50),
            login_window_seconds=_as_int(
                "LOGIN_WINDOW_SECONDS", 900, 60, 86_400
            ),
            web_push_subject=web_push_subject,
            notification_check_seconds=_as_int(
                "NOTIFICATION_CHECK_SECONDS", 900, 60, 86_400
            ),
        )


config = AppConfig.from_env()
