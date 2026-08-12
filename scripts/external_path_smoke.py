#!/usr/bin/env python3
"""Synthetic security contract for a deliberately enabled public HTTPS profile."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient


EXPECTED_ORIGIN = "https://vorrio.example.test"


def require_public_test_environment() -> None:
    expected = {
        "DEPLOYMENT_PROFILE": "public_https",
        "PUBLIC_URL": EXPECTED_ORIGIN,
        "TRUSTED_HOSTS": "vorrio.example.test",
        "ALLOWED_ORIGINS": EXPECTED_ORIGIN,
        "SESSION_HTTPS_ONLY": "true",
        "PUBLIC_EXPOSURE_ACKNOWLEDGED": "true",
    }
    mismatches = [
        name for name, value in expected.items() if os.environ.get(name) != value
    ]
    if mismatches:
        raise RuntimeError(
            "External-path smoke requires its isolated public test profile: "
            + ", ".join(mismatches)
        )


def main() -> None:
    require_public_test_environment()
    from app.main import app

    with TestClient(app, base_url=EXPECTED_ORIGIN) as client:
        readiness = client.get("/api/readiness")
        assert readiness.status_code == 200, readiness.text
        assert readiness.json()["status"] == "ready", readiness.text
        assert all(
            row["status"] == "pass" for row in readiness.json()["checks"]
        ), readiness.text

        shell = client.get("/")
        assert shell.status_code == 200, shell.text
        assert shell.headers["strict-transport-security"].startswith("max-age=")
        assert "default-src 'self'" in shell.headers["content-security-policy"]
        assert shell.headers["cross-origin-opener-policy"] == "same-origin"

        bad_host = client.get("/api/health", headers={"Host": "attacker.example"})
        assert bad_host.status_code == 400, bad_host.text

        bad_origin = client.post(
            "/api/v1/auth/setup",
            headers={"Origin": "https://attacker.example"},
            json={"password": "synthetic-external-path-password"},
        )
        assert bad_origin.status_code == 403, bad_origin.text

        setup = client.post(
            "/api/v1/auth/setup",
            headers={"Origin": EXPECTED_ORIGIN},
            json={
                "password": "synthetic-external-path-password",
                "display_name": "Synthetic Owner",
            },
        )
        assert setup.status_code == 200, setup.text
        cookie = setup.headers.get("set-cookie", "").lower()
        for attribute in ("httponly", "secure", "samesite=lax"):
            assert attribute in cookie, cookie

        api_state = client.get("/api/v1/auth/state")
        assert api_state.status_code == 200, api_state.text
        assert api_state.headers["cache-control"] == "no-store"

        missing_origin = client.post("/api/v1/auth/logout")
        assert missing_origin.status_code == 403, missing_origin.text

        cross_site = client.post(
            "/api/v1/auth/logout",
            headers={"Sec-Fetch-Site": "cross-site"},
        )
        assert cross_site.status_code == 403, cross_site.text

        logout = client.post(
            "/api/v1/auth/logout", headers={"Origin": EXPECTED_ORIGIN}
        )
        assert logout.status_code == 200, logout.text

        trace = client.request("TRACE", "/api/health")
        assert trace.status_code == 405, trace.text

    print("external-path smoke: ready profile, host/origin/cookie/header gates passed")


if __name__ == "__main__":
    main()
