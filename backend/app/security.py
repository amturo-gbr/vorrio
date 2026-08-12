from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


class SecretStore:
    def __init__(self, secret_key: str) -> None:
        digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(digest))

    def encrypt_json(self, value: dict[str, Any]) -> str:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        return self.fernet.encrypt(payload).decode("ascii")

    def decrypt_json(self, value: str | None) -> dict[str, Any]:
        if not value:
            return {}
        try:
            decoded = self.fernet.decrypt(value.encode("ascii"))
        except InvalidToken as exc:
            raise RuntimeError(
                "Gespeicherte Einstellungen können mit APP_SECRET_KEY nicht entschlüsselt werden"
            ) from exc
        return json.loads(decoded.decode("utf-8"))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return "scrypt$" + base64.urlsafe_b64encode(salt).decode("ascii") + "$" + base64.urlsafe_b64encode(derived).decode("ascii")


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_raw, expected_raw = encoded.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_raw.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_raw.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def browser_device_name(user_agent: str | None) -> str:
    """Return a short privacy-safe label without persisting the full user agent."""
    agent = user_agent or ""
    if "iPhone" in agent:
        device = "iPhone"
    elif "iPad" in agent:
        device = "iPad"
    elif "Android" in agent:
        device = "Android-Gerät"
    elif "Macintosh" in agent:
        device = "Mac"
    elif "Windows" in agent:
        device = "Windows-PC"
    elif "Linux" in agent:
        device = "Linux-Gerät"
    else:
        device = "Unbekanntes Gerät"

    if "Edg/" in agent:
        browser = "Edge"
    elif "CriOS/" in agent or "Chrome/" in agent:
        browser = "Chrome"
    elif "FxiOS/" in agent or "Firefox/" in agent:
        browser = "Firefox"
    elif "Safari/" in agent:
        browser = "Safari"
    else:
        browser = "Browser"
    return f"{browser} · {device}"
