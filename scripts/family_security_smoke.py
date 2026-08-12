#!/usr/bin/env python3
"""Run a deterministic family, MFA, recovery and passkey acceptance journey."""

from __future__ import annotations

import base64
import os
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pyotp


test_root = Path(tempfile.mkdtemp(prefix="vorrio-family-security-smoke-"))
os.environ["DATA_DIR"] = str(test_root)
os.environ["APP_SECRET_KEY"] = "family-security-smoke-secret-that-is-long-enough"
os.environ["APP_PASSWORD"] = ""
os.environ["SESSION_HTTPS_ONLY"] = "false"
os.environ["DEPLOYMENT_PROFILE"] = "lan"
os.environ["TRUSTED_HOSTS"] = "testserver,localhost"
os.environ["ALLOWED_ORIGINS"] = "https://testserver"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app, database  # noqa: E402


OWNER_PASSWORD = "sicheres-owner-smoke-passwort"
OWNER_EMAIL = "owner@example.test"


def require(response, expected: int = 200):
    if response.status_code != expected:
        raise AssertionError(
            f"{response.request.method} {response.request.url}: "
            f"{response.status_code} {response.text}"
        )
    return response.json() if response.content else None


with TestClient(app) as owner:
    owner_state = require(
        owner.post(
            "/api/v1/auth/setup",
            json={"password": OWNER_PASSWORD, "display_name": "Owner Smoke"},
        )
    )
    assert owner_state["user"]["role"] == "owner"
    require(
        owner.patch(
            "/api/v1/auth/profile",
            json={"display_name": "Owner Smoke", "email": OWNER_EMAIL},
        )
    )

    experience = require(owner.get("/api/v1/experience"))
    assert experience["onboarding_required"] is True
    require(
        owner.put(
            "/api/v1/experience",
            json={"complete_onboarding": True, "acknowledge_current_version": True},
        )
    )
    with patch.object(app, "version", "9.9.9-smoke"):
        upgraded = require(owner.get("/api/v1/experience"))
        assert upgraded["release_notes_pending"] is True
        acknowledged = require(
            owner.put(
                "/api/v1/experience",
                json={"acknowledge_current_version": True},
            )
        )
        assert acknowledged["release_notes_pending"] is False

    invitation = require(
        owner.post(
            "/api/v1/auth/invitations",
            json={
                "display_name": "Mara Smoke",
                "email": "mara@example.test",
                "role": "member",
                "expires_hours": 72,
            },
        )
    )
    invite_token = invitation["invite_token"]
    with TestClient(app) as member:
        accepted = require(
            member.post(
                f"/api/v1/auth/invitations/{invite_token}/accept",
                json={"password": "sicheres-member-smoke-passwort"},
            )
        )
        assert accepted["user"]["role"] == "member"
        assert member.get("/api/v1/catalog/products").status_code == 200
        assert member.get("/api/v1/settings").status_code == 403
        assert member.post(
            "/api/v1/catalog/products", json={"name": "Nicht erlaubt"}
        ).status_code == 403

        members = require(owner.get("/api/v1/auth/members"))
        mara = next(row for row in members if row["email"] == "mara@example.test")
        changed = require(
            owner.patch(
                f"/api/v1/auth/members/{mara['id']}",
                json={"role": "viewer", "active": True},
            )
        )
        assert changed["role"] == "viewer"
        assert member.get("/api/v1/catalog/products").status_code == 200
        assert member.post(
            "/api/v1/catalog/products", json={"name": "Weiter gesperrt"}
        ).status_code == 403
        blocked = require(
            owner.patch(
                f"/api/v1/auth/members/{mara['id']}",
                json={"role": "viewer", "active": False},
            )
        )
        assert blocked["active"] is False
        assert member.get("/api/v1/catalog/products").status_code == 401

    insecure_passkey = owner.post(
        "/api/v1/auth/passkeys/registration/begin",
        headers={"Origin": "http://testserver"},
        json={"origin": "http://testserver"},
    )
    assert insecure_passkey.status_code == 400
    passkey_begin = require(
        owner.post(
            "/api/v1/auth/passkeys/registration/begin",
            headers={"Origin": "https://testserver"},
            json={"origin": "https://testserver"},
        )
    )
    credential_id = b"vorrio-family-smoke-credential"
    encoded_id = base64.urlsafe_b64encode(credential_id).rstrip(b"=").decode()
    credential = {
        "id": encoded_id,
        "rawId": encoded_id,
        "type": "public-key",
        "response": {"transports": ["internal"]},
        "clientExtensionResults": {},
    }
    registration = SimpleNamespace(
        credential_id=credential_id,
        credential_public_key=b"synthetic-public-key",
        sign_count=0,
        credential_device_type="multi_device",
        credential_backed_up=True,
    )
    with patch("app.main.verify_registration_response", return_value=registration):
        registered = require(
            owner.post(
                "/api/v1/auth/passkeys/registration/complete",
                json={
                    "challenge_id": passkey_begin["challenge_id"],
                    "credential": credential,
                    "name": "Smoke Passkey",
                },
            )
        )
    assert registered["name"] == "Smoke Passkey"

    totp_setup = require(owner.post("/api/v1/auth/totp/setup"))
    fixed_time = int(time.time())
    first_totp = pyotp.TOTP(totp_setup["secret"]).at(fixed_time)
    with patch("app.services.authentication.time.time", return_value=fixed_time):
        enabled = require(
            owner.post("/api/v1/auth/totp/enable", json={"code": first_totp})
        )
    recovery_codes = enabled["recovery_codes"]
    assert len(recovery_codes) == 10
    with database.connect() as connection:
        stored_hashes = [row[0] for row in connection.execute("SELECT code_hash FROM recovery_codes")]
    assert all(code not in stored_hashes for code in recovery_codes)

    require(owner.post("/api/v1/auth/logout"))
    passkey_auth = require(
        owner.post(
            "/api/v1/auth/passkeys/authentication/begin",
            headers={"Origin": "https://testserver"},
            json={"origin": "https://testserver"},
        )
    )
    authentication = SimpleNamespace(
        new_sign_count=1,
        credential_device_type="multi_device",
        credential_backed_up=True,
    )
    with patch("app.main.verify_authentication_response", return_value=authentication):
        passkey_login = require(
            owner.post(
                "/api/v1/auth/passkeys/authentication/complete",
                json={
                    "challenge_id": passkey_auth["challenge_id"],
                    "credential": credential,
                },
            )
        )
    assert passkey_login["authenticated"] is True
    sessions = require(owner.get("/api/v1/auth/sessions"))
    assert sessions[0]["authentication_method"] == "passkey"

    require(owner.post("/api/v1/auth/logout"))
    password_login = require(
        owner.post(
            "/api/v1/auth/login",
            json={"identifier": OWNER_EMAIL, "password": OWNER_PASSWORD},
        )
    )
    assert password_login["authenticated"] is False
    assert password_login["mfa_required"] is True
    second_totp = pyotp.TOTP(totp_setup["secret"]).at(fixed_time + 30)
    with patch("app.services.authentication.time.time", return_value=fixed_time + 30):
        verified = require(
            owner.post(
                "/api/v1/auth/mfa/verify",
                json={
                    "challenge": password_login["mfa_challenge"],
                    "code": second_totp,
                },
            )
        )
    assert verified["authenticated"] is True

    require(owner.post("/api/v1/auth/logout"))
    recovered = require(
        owner.post(
            "/api/v1/auth/recovery",
            json={"identifier": OWNER_EMAIL, "code": recovery_codes[0]},
        )
    )
    assert recovered["authenticated"] is True
    require(
        owner.put(
            "/api/v1/auth/password",
            json={"password": "neues-sicheres-owner-smoke-passwort"},
        )
    )
    require(owner.post("/api/v1/auth/logout"))
    assert owner.post(
        "/api/v1/auth/recovery",
        json={"identifier": OWNER_EMAIL, "code": recovery_codes[0]},
    ).status_code == 401

    with database.connect() as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2
        assert connection.execute(
            "SELECT COUNT(*) FROM webauthn_credentials"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM totp_credentials WHERE enabled=1"
        ).fetchone()[0] == 1

print(
    "Vorrio family/security smoke passed: onboarding -> update note -> invite -> "
    "roles -> block -> passkey -> TOTP -> recovery -> password rotation"
)
