from __future__ import annotations

import base64
import hashlib
import io
import re
import secrets
import time
from urllib.parse import urlsplit

import pyotp
import qrcode
import qrcode.image.svg


RECOVERY_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


class WebAuthnContextError(ValueError):
    pass


def canonical_origin(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise WebAuthnContextError("Ungültige Webadresse")
    if parsed.username or parsed.password or parsed.path not in {"", "/"}:
        raise WebAuthnContextError("Die Webadresse darf keinen Pfad oder Zugang enthalten")
    host = parsed.hostname.lower()
    port = parsed.port
    default_port = (parsed.scheme == "https" and port == 443) or (
        parsed.scheme == "http" and port == 80
    )
    netloc = f"[{host}]" if ":" in host else host
    if port and not default_port:
        netloc += f":{port}"
    return f"{parsed.scheme.lower()}://{netloc}"


def webauthn_context(
    *,
    supplied_origin: str,
    request_origin: str | None,
    allowed_origins: tuple[str, ...],
    public_url: str,
) -> tuple[str, str]:
    origin = canonical_origin(supplied_origin)
    if not request_origin or canonical_origin(request_origin) != origin:
        raise WebAuthnContextError("Webadresse und Browser-Ursprung stimmen nicht überein")
    allowed = {canonical_origin(value) for value in allowed_origins}
    if public_url:
        allowed.add(canonical_origin(public_url))
    if origin not in allowed:
        raise WebAuthnContextError("Diese Webadresse ist nicht für Passkeys freigegeben")
    parsed = urlsplit(origin)
    local_dev = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not local_dev:
        raise WebAuthnContextError("Passkeys benötigen eine stabile HTTPS-Adresse")
    return origin, str(parsed.hostname)


def normalize_recovery_code(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def recovery_code_hash(value: str) -> str:
    return hashlib.sha256(normalize_recovery_code(value).encode("ascii")).hexdigest()


def generate_recovery_codes(count: int = 10) -> list[str]:
    codes: list[str] = []
    while len(codes) < count:
        raw = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(20))
        display = "-".join(raw[index : index + 5] for index in range(0, 20, 5))
        if display not in codes:
            codes.append(display)
    return codes


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, account_name: str, issuer: str = "Vorrio") -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)


def totp_qr_data_uri(uri: str) -> str:
    image = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage, box_size=7)
    output = io.BytesIO()
    image.save(output)
    encoded = base64.b64encode(output.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def verify_totp_step(secret: str, code: str, last_used_step: int | None) -> int | None:
    normalized = re.sub(r"\s", "", code)
    if not re.fullmatch(r"\d{6}", normalized):
        return None
    totp = pyotp.TOTP(secret)
    current_step = int(time.time()) // totp.interval
    for step in range(current_step - 1, current_step + 2):
        if last_used_step is not None and step <= last_used_step:
            continue
        if secrets.compare_digest(totp.at(step * totp.interval), normalized):
            return step
    return None
