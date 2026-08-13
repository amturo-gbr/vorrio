from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import tempfile
import time
import unittest
import zipfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pyotp
from PIL import Image


TEST_DATA_DIR = tempfile.mkdtemp(prefix="grocy-receipt-ai-test-")
os.environ["DATA_DIR"] = TEST_DATA_DIR
os.environ["APP_SECRET_KEY"] = "unit-test-secret-key-that-is-long-enough"
os.environ["APP_PASSWORD"] = ""
os.environ["SESSION_HTTPS_ONLY"] = "false"
os.environ["DEPLOYMENT_PROFILE"] = "lan"
os.environ["TRUSTED_HOSTS"] = "testserver,localhost,127.0.0.1"
os.environ["FORWARDED_ALLOW_IPS"] = "127.0.0.1"
os.environ["ALLOWED_ORIGINS"] = "https://testserver"

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from itsdangerous import TimestampSigner  # noqa: E402

from app.database import (  # noqa: E402
    Database,
    canonical_receipt_key,
    normalize_key,
    retailer_key,
    now_iso,
)
from app.main import app, database, notification_service  # noqa: E402
from app.middleware import PublicExposureGateMiddleware  # noqa: E402
from app.config import config  # noqa: E402
from app.deployment_security import is_safe_secret_key, public_exposure_failures  # noqa: E402
from app.maintenance import rotate_secret  # noqa: E402
from app.security import SecretStore, hash_password  # noqa: E402
from app.services.media import MediaValidationError, validate_image_upload  # noqa: E402
from app.services.pdf_receipt import PdfReceiptError, prepare_pdf_receipt  # noqa: E402
from app.services.grocy import GrocyClient  # noqa: E402
from app.services.matching import match_items, reconcile_unresolved_items  # noqa: E402
from app.services.providers import (  # noqa: E402
    SYSTEM_PROMPT,
    _provider_http_error,
    build_analysis_prompt,
)
from app.services.receipt_identity import build_receipt_fingerprint  # noqa: E402
from app.services.product_candidates import find_product_candidates  # noqa: E402
from app.services.scanning import (  # noqa: E402
    BarcodeValidationError,
    normalize_barcode,
)
from app.services.privacy import sanitize_audit_action  # noqa: E402
from app.services.outbound_urls import (  # noqa: E402
    OutboundUrlError,
    normalize_connector_url,
    validate_public_push_url,
)


class AppFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        database.initialize()
        with database.connect() as conn:
            conn.execute("DELETE FROM household_budget_settings")
            conn.execute("DELETE FROM notification_deliveries")
            conn.execute("DELETE FROM notification_events")
            conn.execute("DELETE FROM push_subscriptions")
            conn.execute("DELETE FROM notification_preferences")
            conn.execute("DELETE FROM api_tokens")
            conn.execute("DELETE FROM webauthn_challenges")
            conn.execute("DELETE FROM login_challenges")
            conn.execute("DELETE FROM recovery_codes")
            conn.execute("DELETE FROM totp_credentials")
            conn.execute("DELETE FROM webauthn_credentials")
            conn.execute("DELETE FROM auth_sessions")
            conn.execute("DELETE FROM household_invitations")
            conn.execute("DELETE FROM household_memberships")
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM households")
            conn.execute("DELETE FROM scan_drafts")
            conn.execute("DELETE FROM shopping_generation_runs")
            conn.execute("DELETE FROM stock_count_sessions")
            conn.execute("DELETE FROM stock_movements")
            conn.execute("DELETE FROM stock_lots")
            conn.execute("DELETE FROM shopping_list_items")
            conn.execute("DELETE FROM import_runs")
            conn.execute("DELETE FROM receipt_items")
            conn.execute("DELETE FROM receipts")
            conn.execute("DELETE FROM catalog_barcodes")
            conn.execute("DELETE FROM catalog_external_refs")
            conn.execute("DELETE FROM catalog_product_variants")
            conn.execute("DELETE FROM catalog_aliases")
            conn.execute("DELETE FROM catalog_product_mappings")
            conn.execute("DELETE FROM catalog_products")
            conn.execute("DELETE FROM catalog_locations")
            conn.execute("DELETE FROM catalog_quantity_units")
            conn.execute("DELETE FROM catalog_product_groups")
            conn.execute("DELETE FROM product_aliases")
            conn.execute("DELETE FROM product_mappings")
            conn.execute("DELETE FROM auth_attempts")
            conn.execute("DELETE FROM audit_events")
            conn.execute("DELETE FROM app_settings")

    def test_privacy_export_retention_operations_and_erasure(self) -> None:
        receipt_file = config.data_dir / "receipts" / "portable-test.jpg"
        receipt_file.parent.mkdir(parents=True, exist_ok=True)
        receipt_file.write_bytes(b"synthetic receipt image")
        external_file = config.data_dir.parent / "must-not-delete.txt"
        external_file.write_text("safe", encoding="utf-8")

        with TestClient(app) as client:
            setup = client.post(
                "/api/v1/auth/setup",
                json={"password": "sicheres-test-passwort", "display_name": "Owner Test"},
            )
            self.assertEqual(setup.status_code, 200)
            self.assertEqual(client.put(
                "/api/v1/experience",
                json={"complete_onboarding": True, "acknowledge_current_version": True},
            ).status_code, 200)
            export_product = database.create_catalog_product(name="Export Testprodukt")
            product_image_file = (
                config.data_dir / "product-images" / f"{export_product['id']}.webp"
            )
            product_image_file.parent.mkdir(parents=True, exist_ok=True)
            product_image_file.write_bytes(b"synthetic product image")
            database.set_catalog_product_image(
                export_product["id"],
                f"/api/v1/catalog/products/{export_product['id']}/image",
            )
            database.create_receipt(
                {
                    "id": "privacy-receipt",
                    "store_name": "Testmarkt",
                    "currency": "EUR",
                    "total": 2.49,
                    "image_path": str(receipt_file),
                },
                [],
            )
            database.create_receipt(
                {
                    "id": "external-path-receipt",
                    "store_name": "Testmarkt",
                    "currency": "EUR",
                    "image_path": str(external_file),
                },
                [],
            )
            old = (datetime.now(UTC) - timedelta(days=30)).isoformat()
            with database.connect() as conn:
                conn.execute("UPDATE receipts SET created_at = ?", (old,))
            database.add_audit_event(
                category="test",
                action="contains_sensitive_details",
                outcome="success",
                source_hash="private-network-fingerprint",
                details={"api_key": "secret-provider-key", "actor_user_id": setup.json()["user"]["id"]},
            )

            preview = client.get("/api/v1/privacy/export/preview")
            self.assertEqual(preview.status_code, 200)
            self.assertEqual(preview.json()["counts"]["products"], 1)
            self.assertEqual(preview.json()["counts"]["receipts"], 2)
            self.assertEqual(preview.json()["receipt_file_count"], 1)
            self.assertEqual(preview.json()["product_image_file_count"], 1)

            exported = client.get("/api/v1/privacy/export?include_receipt_files=true")
            self.assertEqual(exported.status_code, 200)
            self.assertEqual(exported.headers["content-type"], "application/zip")
            archive_bytes = exported.content
            self.assertNotIn(b"secret-provider-key", archive_bytes)
            self.assertNotIn(b"private-network-fingerprint", archive_bytes)
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["format"], "vorrio-portable-export")
                self.assertEqual(manifest["receipt_files_included"], 1)
                self.assertIn("data/catalog.json", archive.namelist())
                self.assertIn("data/receipts.json", archive.namelist())
                preferences = json.loads(archive.read("data/preferences.json"))
                self.assertEqual(
                    preferences["experience"][0]["last_acknowledged_version"],
                    app.version,
                )
                self.assertTrue(any(name.startswith("receipt-files/privacy-receipt") for name in archive.namelist()))
                self.assertIn(
                    f"product-images/{export_product['id']}.webp",
                    archive.namelist(),
                )

            retention = client.get("/api/v1/privacy/retention")
            self.assertEqual(retention.status_code, 200)
            self.assertEqual(retention.json()["expired_file_count"], 2)
            cleaned = client.post("/api/v1/privacy/retention/run")
            self.assertEqual(cleaned.status_code, 200)
            self.assertEqual(cleaned.json()["deleted_file_count"], 1)
            self.assertEqual(cleaned.json()["rejected_path_count"], 1)
            self.assertFalse(receipt_file.exists())
            self.assertTrue(external_file.exists())
            with database.connect() as conn:
                self.assertIsNone(conn.execute(
                    "SELECT image_path FROM receipts WHERE id='privacy-receipt'"
                ).fetchone()[0])
                self.assertEqual(conn.execute(
                    "SELECT image_path FROM receipts WHERE id='external-path-receipt'"
                ).fetchone()[0], str(external_file))

            overview = client.get("/api/v1/operations/overview")
            self.assertEqual(overview.status_code, 200)
            self.assertEqual(overview.json()["database_integrity"], "ok")
            event_payload = json.dumps(overview.json()["recent_events"])
            self.assertNotIn("private-network-fingerprint", event_payload)
            self.assertNotIn("secret-provider-key", event_payload)
            self.assertIn("POST /api/v1/privacy/retention/run", event_payload)

            wrong = client.request(
                "DELETE",
                "/api/v1/privacy/household",
                json={"confirmation": "löschen"},
            )
            self.assertEqual(wrong.status_code, 422)
            erased = client.request(
                "DELETE",
                "/api/v1/privacy/household",
                json={"confirmation": "HAUSHALT ENDGÜLTIG LÖSCHEN"},
            )
            self.assertEqual(erased.status_code, 200)
            self.assertTrue(erased.json()["deleted"])
            self.assertEqual(erased.json()["deleted_product_image_files"], 1)
            self.assertFalse(product_image_file.exists())
            state = client.get("/api/v1/auth/state")
            self.assertFalse(state.json()["authenticated"])
            self.assertTrue(state.json()["needs_setup"])
            with database.connect() as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM catalog_products").fetchone()[0], 0)

    def test_privacy_endpoints_are_owner_only_and_require_recent_authentication(self) -> None:
        with TestClient(app) as client:
            setup = client.post(
                "/api/v1/auth/setup",
                json={"password": "sicheres-test-passwort", "display_name": "Owner Test"},
            )
            self.assertEqual(setup.status_code, 200)
            with database.connect() as conn:
                session_id = conn.execute("SELECT id FROM auth_sessions LIMIT 1").fetchone()[0]
                conn.execute(
                    "UPDATE auth_sessions SET authenticated_at = ? WHERE id = ?",
                    ("2000-01-01T00:00:00+00:00", session_id),
                )
            self.assertEqual(client.get("/api/v1/privacy/export/preview").status_code, 200)
            self.assertEqual(client.get("/api/v1/privacy/export").status_code, 428)
            self.assertEqual(client.post("/api/v1/privacy/retention/run").status_code, 428)
            self.assertEqual(client.request(
                "DELETE",
                "/api/v1/privacy/household",
                json={"confirmation": "HAUSHALT ENDGÜLTIG LÖSCHEN"},
            ).status_code, 428)

    def test_historic_audit_routes_are_sanitized_without_hiding_static_actions(self) -> None:
        self.assertEqual(
            sanitize_audit_action("PATCH /api/v1/scans/571c3d7e-1d7c-4388-95dd-49205353a2e7"),
            "PATCH /api/v1/scans/{id}",
        )
        self.assertEqual(
            sanitize_audit_action("POST /api/v1/receipts/abc/items/item-secret/candidate"),
            "POST /api/v1/receipts/{id}/items/{id}/candidate",
        )
        self.assertEqual(
            sanitize_audit_action("POST /api/v1/scans/resolve"),
            "POST /api/v1/scans/resolve",
        )

    def test_web_push_is_opt_in_encrypted_and_state_deduplicated(self) -> None:
        fake_response = SimpleNamespace(status_code=201)
        with patch.object(notification_service, "sender", return_value=fake_response) as sender:
            with TestClient(app) as client:
                setup = client.post(
                    "/api/v1/auth/setup",
                    json={
                        "password": "sicheres-test-passwort",
                        "display_name": "Owner Test",
                        "preferred_locale": "en",
                    },
                )
                self.assertEqual(setup.status_code, 200)
                state = client.get("/api/v1/notifications/state")
                self.assertEqual(state.status_code, 200)
                self.assertFalse(state.json()["preferences"]["push_enabled"])
                self.assertGreater(len(state.json()["public_key"]), 80)

                endpoint = "https://8.8.8.8/subscriptions/adrian-device"
                registered = client.post(
                    "/api/v1/notifications/subscriptions",
                    json={
                        "endpoint": endpoint,
                        "keys": {"p256dh": "p" * 80, "auth": "a" * 24},
                        "device_name": "iPhone Test",
                    },
                )
                self.assertEqual(registered.status_code, 200)
                subscription_id = registered.json()["id"]
                with database.connect() as conn:
                    stored = conn.execute(
                        "SELECT subscription_encrypted FROM push_subscriptions WHERE id = ?",
                        (subscription_id,),
                    ).fetchone()[0]
                self.assertNotIn(endpoint, stored)
                self.assertEqual(
                    SecretStore(config.secret_key).decrypt_json(stored)["endpoint"], endpoint
                )

                product = database.create_catalog_product(
                    name="Haferdrink Push Test",
                    minimum_stock_quantity=2,
                    shopping_target_quantity=4,
                )
                enabled = client.put(
                    "/api/v1/notifications/preferences",
                    json={
                        "push_enabled": True,
                        "low_stock_enabled": True,
                        "expiry_enabled": False,
                        "expiry_days_before": 7,
                    },
                )
                self.assertEqual(enabled.status_code, 200)
                first_delivery_count = sender.call_count
                self.assertGreaterEqual(first_delivery_count, 1)
                first = notification_service.evaluate_and_send()
                self.assertEqual(first["events"], 0)
                self.assertEqual(sender.call_count, first_delivery_count)

                timestamp = "2026-08-12T12:00:00+00:00"
                with database.connect() as conn:
                    conn.execute(
                        """
                        INSERT INTO stock_lots(
                            id, product_id, quantity, created_at, updated_at
                        ) VALUES ('push-stock-lot', ?, 3, ?, ?)
                        """,
                        (product["id"], timestamp, timestamp),
                    )
                notification_service.evaluate_and_send()
                with database.connect() as conn:
                    conn.execute("DELETE FROM stock_lots WHERE id = 'push-stock-lot'")
                second = notification_service.evaluate_and_send()
                self.assertEqual(second["events"], 1)
                self.assertEqual(sender.call_count, first_delivery_count + 1)
                stock_payload = json.loads(sender.call_args.kwargs["data"])
                self.assertEqual(stock_payload["locale"], "en")
                self.assertEqual(stock_payload["title"], "Stock is running low")

                tested = client.post(
                    "/api/v1/notifications/test",
                    json={"subscription_id": subscription_id},
                )
                self.assertEqual(tested.status_code, 200)
                self.assertEqual(tested.json()["delivered"], 1)
                self.assertEqual(sender.call_count, first_delivery_count + 2)
                test_payload = json.loads(sender.call_args.kwargs["data"])
                self.assertEqual(test_payload["locale"], "en")
                self.assertEqual(test_payload["title"], "Vorrio is ready")
                revoked = client.delete(
                    f"/api/v1/notifications/subscriptions/{subscription_id}"
                )
                self.assertEqual(revoked.status_code, 200)

    def test_expiry_push_respects_personal_warning_window(self) -> None:
        fake_response = SimpleNamespace(status_code=201)
        with patch.object(notification_service, "sender", return_value=fake_response) as sender:
            with TestClient(app) as client:
                client.post(
                    "/api/v1/auth/setup",
                    json={"password": "sicheres-test-passwort", "display_name": "Owner Test"},
                )
                registered = client.post(
                    "/api/v1/notifications/subscriptions",
                    json={
                        "endpoint": "https://8.8.4.4/subscriptions/expiry-device",
                        "keys": {"p256dh": "p" * 80, "auth": "a" * 24},
                        "device_name": "Ablauf Test",
                    },
                )
                self.assertEqual(registered.status_code, 200)
                product = database.create_catalog_product(name="Joghurt Ablauf Test")
                best_before = (datetime.now(UTC).date() + timedelta(days=3)).isoformat()
                with database.connect() as conn:
                    conn.execute(
                        """
                        INSERT INTO stock_lots(
                            id, product_id, quantity, best_before_date, created_at, updated_at
                        ) VALUES ('expiry-stock-lot', ?, 1, ?, ?, ?)
                        """,
                        (product["id"], best_before, now_iso(), now_iso()),
                    )
                enabled = client.put(
                    "/api/v1/notifications/preferences",
                    json={
                        "push_enabled": True,
                        "low_stock_enabled": False,
                        "expiry_enabled": True,
                        "expiry_days_before": 7,
                    },
                )
                self.assertEqual(enabled.status_code, 200)
                self.assertEqual(sender.call_count, 1)
                state = client.get("/api/v1/notifications/state").json()
                self.assertEqual(state["active_expiry_events"], 1)
                self.assertEqual(notification_service.evaluate_and_send()["events"], 0)

    def test_scoped_api_tokens_are_hashed_expiring_and_revocable(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(
                client.post(
                    "/api/v1/auth/setup",
                    json={"password": "sicheres-test-passwort", "display_name": "Owner Test"},
                ).status_code,
                200,
            )
            scopes = client.get("/api/v1/auth/api-token-scopes")
            self.assertEqual(scopes.status_code, 200)
            self.assertEqual(len(scopes.json()), 7)

            created = client.post(
                "/api/v1/auth/api-tokens",
                json={
                    "name": "Home Assistant",
                    "scopes": ["status:read"],
                    "expires_days": 30,
                },
            )
            self.assertEqual(created.status_code, 200)
            token = created.json()["token"]
            token_id = created.json()["id"]
            self.assertTrue(token.startswith("vor_pat_"))
            listed = client.get("/api/v1/auth/api-tokens")
            self.assertEqual(listed.status_code, 200)
            self.assertNotIn("token", listed.json()[0])

            with database.connect() as conn:
                stored = conn.execute(
                    "SELECT token_hash FROM api_tokens WHERE id = ?", (token_id,)
                ).fetchone()[0]
            self.assertEqual(stored, hashlib.sha256(token.encode()).hexdigest())
            self.assertNotEqual(stored, token)

            bearer = {"Authorization": f"Bearer {token}"}
            self.assertEqual(client.get("/api/v1/status", headers=bearer).status_code, 200)
            self.assertEqual(client.get("/api/v1/shopping-list", headers=bearer).status_code, 403)
            self.assertEqual(client.get("/api/v1/auth/me", headers=bearer).status_code, 403)
            self.assertEqual(
                client.get("/api/v1/status", headers={"Authorization": "Bearer invalid"}).status_code,
                401,
            )

            scanner = client.post(
                "/api/v1/auth/api-tokens",
                json={
                    "name": "Handscanner",
                    "scopes": ["scans:write"],
                    "expires_days": 90,
                },
            )
            self.assertEqual(scanner.status_code, 200)
            scanner_header = {"Authorization": f"Bearer {scanner.json()['token']}"}
            invalid_scan = client.post(
                "/api/v1/scans/resolve",
                headers=scanner_header,
                json={
                    "barcode": "x",
                    "mode": "identify",
                    "client_mutation_id": "api-token-scope-test",
                },
            )
            self.assertEqual(invalid_scan.status_code, 422)
            self.assertEqual(client.get("/api/v1/scans/unresolved", headers=scanner_header).status_code, 403)

            self.assertEqual(
                client.delete(f"/api/v1/auth/api-tokens/{token_id}").status_code,
                200,
            )
            self.assertEqual(client.get("/api/v1/status", headers=bearer).status_code, 401)
            with database.connect() as conn:
                conn.execute(
                    "UPDATE api_tokens SET expires_at = '2000-01-01T00:00:00+00:00' WHERE id = ?",
                    (scanner.json()["id"],),
                )
            self.assertEqual(client.post(
                "/api/v1/scans/resolve",
                headers=scanner_header,
                json={
                    "barcode": "x",
                    "mode": "identify",
                    "client_mutation_id": "api-token-expiry-test",
                },
            ).status_code, 401)

            actions = {event["action"] for event in database.list_audit_events(30)}
            self.assertIn("api_token_create", actions)
            self.assertIn("api_token_revoke", actions)

    def test_totp_recovery_codes_and_recent_authentication(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(
                client.post(
                    "/api/v1/auth/setup",
                    json={"password": "sicheres-test-passwort", "display_name": "Owner Test"},
                ).status_code,
                200,
            )
            self.assertEqual(
                client.patch(
                    "/api/v1/auth/profile",
                    json={"display_name": "Owner Test", "email": "owner@example.test"},
                ).status_code,
                200,
            )
            setup = client.post("/api/v1/auth/totp/setup")
            self.assertEqual(setup.status_code, 200)
            secret = setup.json()["secret"]
            fixed = int(time.time())
            first_code = pyotp.TOTP(secret).at(fixed)
            with patch("app.services.authentication.time.time", return_value=fixed):
                enabled = client.post("/api/v1/auth/totp/enable", json={"code": first_code})
            self.assertEqual(enabled.status_code, 200)
            recovery_codes = enabled.json()["recovery_codes"]
            self.assertEqual(len(recovery_codes), 10)
            with database.connect() as conn:
                stored = [row[0] for row in conn.execute("SELECT code_hash FROM recovery_codes")]
            self.assertTrue(all(code not in stored for code in recovery_codes))

            client.post("/api/v1/auth/logout")
            password = client.post(
                "/api/v1/auth/login",
                json={"identifier": "owner@example.test", "password": "sicheres-test-passwort"},
            )
            self.assertFalse(password.json()["authenticated"])
            self.assertTrue(password.json()["mfa_required"])
            second_code = pyotp.TOTP(secret).at(fixed + 30)
            with patch("app.services.authentication.time.time", return_value=fixed + 30):
                verified = client.post(
                    "/api/v1/auth/mfa/verify",
                    json={"challenge": password.json()["mfa_challenge"], "code": second_code},
                )
            self.assertEqual(verified.status_code, 200)
            self.assertTrue(verified.json()["authenticated"])

            client.post("/api/v1/auth/logout")
            recovered = client.post(
                "/api/v1/auth/recovery",
                json={"identifier": "owner@example.test", "code": recovery_codes[0]},
            )
            self.assertEqual(recovered.status_code, 200)
            changed = client.put(
                "/api/v1/auth/password", json={"password": "noch-sichereres-passwort"}
            )
            self.assertEqual(changed.status_code, 200)
            client.post("/api/v1/auth/logout")
            self.assertEqual(
                client.post(
                    "/api/v1/auth/recovery",
                    json={"identifier": "owner@example.test", "code": recovery_codes[0]},
                ).status_code,
                401,
            )

    def test_passkey_registration_login_and_secure_origin_contract(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/api/v1/auth/setup",
                json={"password": "sicheres-test-passwort", "display_name": "Owner Test"},
            )
            insecure = client.post(
                "/api/v1/auth/passkeys/registration/begin",
                headers={"Origin": "http://testserver"},
                json={"origin": "http://testserver"},
            )
            self.assertEqual(insecure.status_code, 400)

            begin = client.post(
                "/api/v1/auth/passkeys/registration/begin",
                headers={"Origin": "https://testserver"},
                json={"origin": "https://testserver"},
            )
            self.assertEqual(begin.status_code, 200)
            credential_id = b"vorrio-test-credential"
            encoded_id = base64.urlsafe_b64encode(credential_id).rstrip(b"=").decode("ascii")
            credential = {
                "id": encoded_id,
                "rawId": encoded_id,
                "type": "public-key",
                "response": {"transports": ["internal"]},
                "clientExtensionResults": {},
            }
            registration = SimpleNamespace(
                credential_id=credential_id,
                credential_public_key=b"public-key",
                sign_count=0,
                credential_device_type="multi_device",
                credential_backed_up=True,
            )
            with patch("app.main.verify_registration_response", return_value=registration):
                complete = client.post(
                    "/api/v1/auth/passkeys/registration/complete",
                    json={
                        "challenge_id": begin.json()["challenge_id"],
                        "credential": credential,
                        "name": "Test-Passkey",
                    },
                )
            self.assertEqual(complete.status_code, 200)
            self.assertEqual(complete.json()["name"], "Test-Passkey")
            client.post("/api/v1/auth/logout")

            auth_begin = client.post(
                "/api/v1/auth/passkeys/authentication/begin",
                headers={"Origin": "https://testserver"},
                json={"origin": "https://testserver"},
            )
            authentication = SimpleNamespace(
                new_sign_count=1,
                credential_device_type="multi_device",
                credential_backed_up=True,
            )
            with patch("app.main.verify_authentication_response", return_value=authentication):
                logged_in = client.post(
                    "/api/v1/auth/passkeys/authentication/complete",
                    json={
                        "challenge_id": auth_begin.json()["challenge_id"],
                        "credential": credential,
                    },
                )
            self.assertEqual(logged_in.status_code, 200)
            self.assertTrue(logged_in.json()["authenticated"])
            sessions = client.get("/api/v1/auth/sessions").json()
            self.assertEqual(sessions[0]["authentication_method"], "passkey")

    def test_sensitive_changes_require_recent_authentication(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/api/v1/auth/setup",
                json={"password": "sicheres-test-passwort", "display_name": "Owner Test"},
            )
            with database.connect() as conn:
                conn.execute(
                    "UPDATE auth_sessions SET authenticated_at = '2000-01-01T00:00:00+00:00'"
                )
            state = client.get("/api/v1/auth/security")
            self.assertFalse(state.json()["recent_authentication"])
            self.assertEqual(client.post("/api/v1/auth/recovery-codes").status_code, 428)
            confirmed = client.post(
                "/api/v1/auth/reauthenticate",
                json={"password": "sicheres-test-passwort"},
            )
            self.assertEqual(confirmed.status_code, 200)
            self.assertTrue(confirmed.json()["recent_authentication"])
            self.assertEqual(client.post("/api/v1/auth/recovery-codes").status_code, 200)

    def test_first_run_auth_and_encrypted_settings(self) -> None:
        with TestClient(app) as client:
            state = client.get("/api/auth/state")
            self.assertEqual(state.status_code, 200)
            self.assertTrue(state.json()["needs_setup"])

            setup = client.post(
                "/api/auth/setup", json={"password": "sicheres-test-passwort"}
            )
            self.assertEqual(setup.status_code, 200)
            self.assertTrue(setup.json()["authenticated"])

            payload = {
                "grocy": {
                    "url": "http://grocy.test",
                    "api_key": "grocy-secret",
                },
                "provider": {
                    "type": "cortecs",
                    "base_url": "https://api.cortecs.ai/v1",
                    "model": "vision-model",
                    "api_key": "provider-secret",
                },
                "privacy": {
                    "delete_image_after_analysis": True,
                    "retention_days": 0,
                },
            }
            saved = client.put("/api/settings", json=payload)
            self.assertEqual(saved.status_code, 200)
            public = saved.json()
            self.assertNotIn("api_key", public["grocy"])
            self.assertNotIn("api_key", public["provider"])
            self.assertTrue(public["grocy"]["api_key_configured"])
            self.assertTrue(public["provider"]["api_key_configured"])

            encrypted = database.get_setting("connections.v1") or ""
            self.assertNotIn("grocy-secret", encrypted)
            self.assertNotIn("provider-secret", encrypted)

            client.post("/api/auth/logout")
            self.assertEqual(client.get("/api/settings").status_code, 401)
            self.assertEqual(
                client.post(
                    "/api/auth/login", json={"password": "falsch-falsch"}
                ).status_code,
                401,
            )
            self.assertEqual(
                client.post(
                    "/api/auth/login", json={"password": "sicheres-test-passwort"}
                ).status_code,
                200,
            )

    def test_named_owner_and_revocable_device_sessions(self) -> None:
        with TestClient(app) as first:
            setup = first.post(
                "/api/v1/auth/setup",
                json={
                    "password": "sicheres-test-passwort",
                    "display_name": "Owner Test",
                },
            )
            self.assertEqual(setup.status_code, 200)
            self.assertEqual(setup.json()["user"]["display_name"], "Owner Test")
            self.assertEqual(setup.json()["user"]["role"], "owner")
            self.assertFalse(setup.json()["needs_owner_setup"])

            profile = first.patch(
                "/api/v1/auth/profile",
                json={"display_name": "Owner Test", "email": "owner@example.test"},
            )
            self.assertEqual(profile.status_code, 200)
            self.assertEqual(profile.json()["user"]["email"], "owner@example.test")

            with TestClient(app) as second:
                login = second.post(
                    "/api/v1/auth/login",
                    json={"password": "sicheres-test-passwort"},
                )
                self.assertEqual(login.status_code, 200)

                sessions = first.get("/api/v1/auth/sessions")
                self.assertEqual(sessions.status_code, 200)
                self.assertEqual(len(sessions.json()), 2)
                self.assertEqual(sum(1 for item in sessions.json() if item["current"]), 1)
                other = next(item for item in sessions.json() if not item["current"])

                revoked = first.delete(f"/api/v1/auth/sessions/{other['id']}")
                self.assertEqual(revoked.status_code, 200)
                self.assertEqual(revoked.json()["revoked"], 1)
                self.assertEqual(second.get("/api/v1/settings").status_code, 401)
                self.assertEqual(first.get("/api/v1/settings").status_code, 200)

            events = database.list_audit_events(20)
            actions = {event["action"] for event in events}
            self.assertIn("owner_profile_update", actions)
            self.assertIn("session_revoke", actions)

    def test_personal_onboarding_and_release_notes_are_acknowledged_once(self) -> None:
        with TestClient(app) as client:
            setup = client.post(
                "/api/v1/auth/setup",
                json={"password": "sicheres-test-passwort", "display_name": "Owner Test"},
            )
            self.assertEqual(setup.status_code, 200)

            first = client.get("/api/v1/experience")
            self.assertEqual(first.status_code, 200)
            self.assertTrue(first.json()["onboarding_required"])
            self.assertFalse(first.json()["release_notes_pending"])
            self.assertEqual(first.json()["release"]["version"], app.version)

            empty_update = client.put("/api/v1/experience", json={})
            self.assertEqual(empty_update.status_code, 422)

            completed = client.put(
                "/api/v1/experience",
                json={
                    "complete_onboarding": True,
                    "acknowledge_current_version": True,
                },
            )
            self.assertEqual(completed.status_code, 200)
            self.assertTrue(completed.json()["onboarding_completed"])
            self.assertFalse(completed.json()["onboarding_required"])
            self.assertFalse(completed.json()["release_notes_pending"])
            self.assertEqual(completed.json()["last_acknowledged_version"], app.version)

            with patch.object(app, "version", "0.8.24"):
                upgraded = client.get("/api/v1/experience")
                self.assertTrue(upgraded.json()["release_notes_pending"])
                self.assertEqual(upgraded.json()["release"]["version"], "0.8.24")
                acknowledged = client.put(
                    "/api/v1/experience",
                    json={"acknowledge_current_version": True},
                )
                self.assertFalse(acknowledged.json()["release_notes_pending"])
                self.assertEqual(
                    acknowledged.json()["last_acknowledged_version"], "0.8.24"
                )

            with database.connect() as conn:
                exported_experience = conn.execute(
                    "SELECT onboarding_completed_at, last_acknowledged_version FROM user_experience"
                ).fetchone()
                self.assertIsNotNone(exported_experience["onboarding_completed_at"])
                self.assertEqual(exported_experience["last_acknowledged_version"], "0.8.24")
                actions = {
                    row[0]
                    for row in conn.execute(
                        "SELECT action FROM audit_events WHERE category = 'experience'"
                    ).fetchall()
                }
            self.assertIn("experience_update", actions)

    def test_interface_locale_is_personal_persisted_and_validated(self) -> None:
        with TestClient(app) as client:
            setup = client.post(
                "/api/v1/auth/setup",
                json={
                    "password": "sicheres-test-passwort",
                    "display_name": "Owner Test",
                    "preferred_locale": "en",
                },
            )
            self.assertEqual(setup.status_code, 200)
            self.assertEqual(setup.json()["user"]["preferred_locale"], "en")
            master_data = client.get("/api/v1/catalog/master-data")
            self.assertEqual(master_data.status_code, 200)
            self.assertIn(
                "Pantry",
                {item["name"] for item in master_data.json()["locations"]},
            )
            self.assertIn(
                "Package",
                {item["name"] for item in master_data.json()["quantity_units"]},
            )
            self.assertIn(
                "Food",
                {item["name"] for item in master_data.json()["product_groups"]},
            )
            self.assertEqual(
                client.get("/api/v1/experience").json()["release"]["title"],
                "Languages become modular",
            )
            scopes = client.get("/api/v1/auth/api-token-scopes")
            self.assertEqual(scopes.status_code, 200)
            self.assertEqual(scopes.json()[0]["label"], "Read status")

            changed = client.patch(
                "/api/v1/auth/preferences",
                json={"preferred_locale": "de"},
            )
            self.assertEqual(changed.status_code, 200)
            self.assertEqual(changed.json()["user"]["preferred_locale"], "de")
            self.assertIn(
                "Pantry",
                {
                    item["name"]
                    for item in client.get("/api/v1/catalog/master-data").json()["locations"]
                },
            )
            self.assertEqual(
                client.get("/api/v1/experience").json()["release"]["title"],
                "Sprachen werden modular",
            )
            self.assertEqual(
                client.patch(
                    "/api/v1/auth/preferences",
                    json={"preferred_locale": "fr"},
                ).status_code,
                422,
            )
            events = database.list_audit_events(20)
            self.assertIn("user_locale_update", {event["action"] for event in events})

    def test_single_use_family_invitation_login_and_role_enforcement(self) -> None:
        with TestClient(app) as owner:
            setup = owner.post(
                "/api/v1/auth/setup",
                json={
                    "password": "sicheres-owner-passwort",
                    "display_name": "Owner Test",
                },
            )
            self.assertEqual(setup.status_code, 200)
            missing_email = owner.post(
                "/api/v1/auth/invitations",
                json={
                    "display_name": "Mara Mitglied",
                    "email": "mara@example.test",
                    "role": "member",
                },
            )
            self.assertEqual(missing_email.status_code, 409)
            self.assertEqual(
                owner.patch(
                    "/api/v1/auth/profile",
                    json={"display_name": "Owner Test", "email": "owner@example.test"},
                ).status_code,
                200,
            )
            created = owner.post(
                "/api/v1/auth/invitations",
                json={
                    "display_name": "Mara Mitglied",
                    "email": "mara@example.test",
                    "role": "member",
                    "expires_hours": 72,
                },
            )
            self.assertEqual(created.status_code, 200)
            invitation = created.json()
            token = invitation["invite_token"]
            self.assertTrue(token)
            with database.connect() as conn:
                stored = conn.execute(
                    "SELECT token_hash FROM household_invitations WHERE id = ?",
                    (invitation["id"],),
                ).fetchone()[0]
            self.assertNotEqual(stored, token)

            public = owner.get(f"/api/v1/auth/invitations/{token}")
            self.assertEqual(public.status_code, 200)
            self.assertEqual(public.json()["role"], "member")

            with TestClient(app) as member:
                accepted = member.post(
                    f"/api/v1/auth/invitations/{token}/accept",
                    json={
                        "password": "eigenes-mitglied-passwort",
                        "preferred_locale": "en",
                    },
                )
                self.assertEqual(accepted.status_code, 200)
                self.assertEqual(accepted.json()["user"]["role"], "member")
                self.assertEqual(accepted.json()["user"]["preferred_locale"], "en")
                self.assertTrue(accepted.json()["identifier_required"])
                self.assertEqual(
                    member.post(
                        f"/api/v1/auth/invitations/{token}/accept",
                        json={"password": "anderes-passwort"},
                    ).status_code,
                    410,
                )
                self.assertEqual(member.get("/api/v1/catalog/products").status_code, 200)
                self.assertEqual(member.get("/api/v1/settings").status_code, 403)
                self.assertEqual(
                    member.post(
                        "/api/v1/catalog/products", json={"name": "Nicht erlaubt"}
                    ).status_code,
                    403,
                )

                with TestClient(app) as signed_out:
                    self.assertTrue(
                        signed_out.get("/api/v1/auth/state").json()["identifier_required"]
                    )
                    self.assertEqual(
                        signed_out.post(
                            "/api/v1/auth/login",
                            json={"password": "sicheres-owner-passwort"},
                        ).status_code,
                        401,
                    )
                    self.assertEqual(
                        signed_out.post(
                            "/api/v1/auth/login",
                            json={
                                "identifier": "owner@example.test",
                                "password": "sicheres-owner-passwort",
                            },
                        ).status_code,
                        200,
                    )

                members = owner.get("/api/v1/auth/members").json()
                mara = next(row for row in members if row["email"] == "mara@example.test")
                changed = owner.patch(
                    f"/api/v1/auth/members/{mara['id']}",
                    json={"role": "viewer", "active": True},
                )
                self.assertEqual(changed.status_code, 200)
                self.assertEqual(changed.json()["role"], "viewer")
                self.assertEqual(member.get("/api/v1/catalog/products").status_code, 200)
                self.assertEqual(
                    member.post(
                        "/api/v1/catalog/products", json={"name": "Weiter gesperrt"}
                    ).status_code,
                    403,
                )
                blocked = owner.patch(
                    f"/api/v1/auth/members/{mara['id']}",
                    json={"role": "viewer", "active": False},
                )
                self.assertEqual(blocked.status_code, 200)
                self.assertFalse(blocked.json()["active"])
                self.assertEqual(member.get("/api/v1/catalog/products").status_code, 401)

            self.assertFalse(owner.get("/api/v1/auth/state").json()["identifier_required"])

    def test_admin_can_manage_members_but_not_owner_connectors_or_admins(self) -> None:
        with TestClient(app) as owner:
            owner.post(
                "/api/v1/auth/setup",
                json={"password": "sicheres-owner-passwort", "display_name": "Owner"},
            )
            owner.patch(
                "/api/v1/auth/profile",
                json={"display_name": "Owner", "email": "owner@example.test"},
            )
            invite = owner.post(
                "/api/v1/auth/invitations",
                json={
                    "display_name": "Alex Admin",
                    "email": "alex@example.test",
                    "role": "admin",
                },
            ).json()
            with TestClient(app) as admin:
                accepted = admin.post(
                    f"/api/v1/auth/invitations/{invite['invite_token']}/accept",
                    json={"password": "sicheres-admin-passwort"},
                )
                self.assertEqual(accepted.status_code, 200)
                self.assertEqual(admin.get("/api/v1/auth/members").status_code, 200)
                self.assertEqual(admin.get("/api/v1/settings").status_code, 403)
                product = admin.post(
                    "/api/v1/catalog/products", json={"name": "Admin Produkt"}
                )
                self.assertEqual(product.status_code, 200)
                forbidden = admin.post(
                    "/api/v1/auth/invitations",
                    json={
                        "display_name": "Noch ein Admin",
                        "email": "admin2@example.test",
                        "role": "admin",
                    },
                )
                self.assertEqual(forbidden.status_code, 403)

    def test_legacy_signed_session_is_upgraded_without_logout(self) -> None:
        with TestClient(app) as client:
            database.put_setting(
                "auth.password_hash", hash_password("sicheres-test-passwort")
            )
            legacy_payload = base64.b64encode(
                json.dumps({"authenticated": True}).encode("utf-8")
            )
            client.cookies.set(
                "session",
                TimestampSigner(config.secret_key).sign(legacy_payload).decode("utf-8"),
            )
            state = client.get("/api/v1/auth/state")
            self.assertEqual(state.status_code, 200)
            self.assertTrue(state.json()["authenticated"])
            self.assertTrue(state.json()["needs_owner_setup"])
            self.assertEqual(len(client.get("/api/v1/auth/sessions").json()), 1)

    def test_normalize_key_handles_german_product_names(self) -> None:
        self.assertEqual(normalize_key("  H-Milch 1,5 %  "), "h milch 1 5")
        self.assertEqual(normalize_key("Käse & Öl"), "kaese oel")

    def test_receipt_keys_ignore_prices_quantities_and_retailer_variants(self) -> None:
        self.assertEqual(canonical_receipt_key("FRISCHKAESE NATU 1,59 B"), "frischkaese natu")
        self.assertEqual(
            canonical_receipt_key("HIGHPRO KIR-/ARO 2 STK X1,49 2,98 B"),
            "highpro kir aro",
        )
        self.assertEqual(retailer_key("REWE Ali Akay ohG"), "rewe")
        self.assertEqual(retailer_key("dm-drogerie markt Bad Soden"), "dm")

    def test_confirmed_mapping_creates_cross_store_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "aliases.db")
            local.initialize()
            local.create_receipt(
                {"id": "receipt-1", "store_name": "REWE Bad Soden"},
                [
                    {
                        "id": "item-1",
                        "raw_name": "FRISCHKAESE NATU 1,59 B",
                        "normalized_name": "Frischkäse Natur",
                    }
                ],
            )
            self.assertTrue(
                local.update_item_mapping(
                    "receipt-1", "item-1", 7, "Frischkäse Natur", True
                )
            )
            alias = local.get_alias("Frischkäse Natur", "Frischkäse Natur")
            self.assertIsNotNone(alias)
            self.assertEqual(alias["grocy_product_id"], 7)

    def test_duplicate_hash_is_scoped_to_analysis_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "hashes.db")
            local.initialize()
            local.create_receipt(
                {
                    "id": "receipt-1",
                    "store_name": "REWE",
                    "source_sha256": "same-file",
                    "analysis_version": "0.4.0",
                },
                [{"id": "item-1", "raw_name": "Bananen"}],
            )
            self.assertEqual(
                local.get_receipt_by_hash("same-file", "0.4.0")["id"],
                "receipt-1",
            )
            self.assertIsNone(local.get_receipt_by_hash("same-file", "0.3.2"))

    def test_semantic_receipt_fingerprint_detects_a_second_capture(self) -> None:
        receipt = {
            "store_name": "REWE Bad Soden",
            "purchase_date": "2026-08-10",
            "currency": "EUR",
            "total": 3.78,
        }
        first = build_receipt_fingerprint(
            receipt,
            [
                {"raw_name": "HAFERDRINK 1L", "quantity": 1, "total_price": 2.49},
                {"raw_name": "JOGHURT NATUR", "quantity": 1, "total_price": 1.29},
            ],
        )
        second = build_receipt_fingerprint(
            receipt,
            [
                {"normalized_name": "Joghurt Natur", "quantity": 1, "total_price": 1.29},
                {"normalized_name": "Haferdrink 1l", "quantity": 1, "total_price": 2.49},
            ],
        )
        self.assertIsNotNone(first)
        self.assertEqual(first, second)

        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "fingerprint.db")
            local.initialize()
            local.create_receipt(
                {**receipt, "id": "receipt-1", "receipt_fingerprint": first},
                [
                    {"id": "item-1", "raw_name": "HAFERDRINK 1L"},
                    {"id": "item-2", "raw_name": "JOGHURT NATUR"},
                ],
            )
            self.assertEqual(
                local.get_receipt_by_fingerprint(str(second))["id"], "receipt-1"
            )

    def test_catalog_purchase_is_local_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "catalog.db")
            local.initialize()
            master = local.catalog_master_data()
            product = local.create_catalog_product(
                name="Haferdrink",
                location_id=master["locations"][0]["id"],
                quantity_unit_id=master["quantity_units"][0]["id"],
                brand="Testmarke",
                barcode="4000000000016",
                default_best_before_days=30,
            )
            local.create_receipt(
                {"id": "receipt-1", "store_name": "REWE", "purchase_date": "2026-08-10"},
                [
                    {
                        "id": "item-1",
                        "raw_name": "HAFERDRINK",
                        "normalized_name": "Haferdrink",
                    }
                ],
            )
            self.assertTrue(
                local.update_catalog_item_mapping(
                    "receipt-1", "item-1", product["id"], True
                )
            )
            self.assertTrue(local.record_catalog_purchase("receipt-1", "item-1"))
            self.assertFalse(local.record_catalog_purchase("receipt-1", "item-1"))
            self.assertEqual(local.catalog_summary()["stock_lots"], 1)
            self.assertEqual(
                local.catalog_product_by_barcode("4000000000016")["id"], product["id"]
            )
            history = local.catalog_price_history(product["id"])
            self.assertEqual(history[0]["brand"], "Testmarke")
            self.assertEqual(history[0]["catalog_variant_id"], local.catalog_product_by_barcode("4000000000016")["variant_id"])

    def test_price_insights_compare_only_confirmed_receipt_prices(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "prices.db")
            local.initialize()
            product = local.create_catalog_product(name="Haferdrink")
            purchases = [
                ("receipt-rewe", "item-rewe", "REWE Markt", "REWE", "2026-08-10", 2.49),
                ("receipt-dm", "item-dm", "dm Bad Soden", "dm", "2026-08-09", 2.29),
            ]
            for receipt_id, item_id, store_name, retailer, date, price in purchases:
                local.create_receipt(
                    {
                        "id": receipt_id,
                        "store_name": store_name,
                        "retailer": retailer,
                        "purchase_date": date,
                    },
                    [{"id": item_id, "raw_name": "HAFERDRINK", "unit_price": price}],
                )
                self.assertTrue(local.update_catalog_item_mapping(receipt_id, item_id, product["id"], True))
                self.assertTrue(local.record_catalog_purchase(receipt_id, item_id))

            local.create_receipt(
                {"id": "receipt-draft", "store_name": "ALDI", "purchase_date": "2026-08-11"},
                [{"id": "item-draft", "raw_name": "HAFERDRINK", "unit_price": 0.49}],
            )
            self.assertTrue(local.update_catalog_item_mapping("receipt-draft", "item-draft", product["id"], True))

            insight = local.price_insights()
            self.assertEqual(insight["product_count"], 1)
            self.assertEqual(insight["store_count"], 2)
            self.assertEqual(insight["observation_count"], 2)
            summary = insight["products"][0]
            self.assertEqual(summary["latest_price"], 2.49)
            self.assertEqual(summary["lowest_price"], 2.29)
            self.assertEqual(summary["change_amount"], 0.2)
            self.assertEqual([store["store_key"] for store in summary["stores"]], ["dm", "rewe"])
            self.assertEqual(len(local.catalog_price_history(product["id"])), 2)

    def test_price_insights_api_requires_authentication(self) -> None:
        product = database.create_catalog_product(name="Preis-API-Testprodukt")
        database.create_receipt(
            {
                "id": "price-api-receipt",
                "store_name": "REWE Testmarkt",
                "retailer": "REWE",
                "purchase_date": "2026-08-11",
            },
            [{"id": "price-api-item", "raw_name": "TESTPRODUKT", "unit_price": 1.99}],
        )
        self.assertTrue(
            database.update_catalog_item_mapping(
                "price-api-receipt", "price-api-item", product["id"], True
            )
        )
        self.assertTrue(database.record_catalog_purchase("price-api-receipt", "price-api-item"))

        with TestClient(app) as client:
            self.assertEqual(client.get("/api/v1/insights/prices").status_code, 401)
            setup = client.post(
                "/api/v1/auth/setup", json={"password": "sicheres-preis-passwort"}
            )
            self.assertEqual(setup.status_code, 200)
            response = client.get("/api/v1/insights/prices")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            summary = next(
                item for item in payload["products"]
                if item["product_id"] == product["id"]
            )
            self.assertEqual(summary["latest_price"], 1.99)

    def test_budget_overview_uses_only_confirmed_receipts_and_reports_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "budget.db")
            local.initialize()
            owner = local.ensure_owner_identity()
            product = local.create_catalog_product(name="Haushaltseinkauf")

            def add_confirmed(
                receipt_id: str,
                purchase_date: str,
                total: float | None,
                retailer: str,
                currency: str = "EUR",
            ) -> None:
                item_id = f"{receipt_id}-item"
                local.create_receipt(
                    {
                        "id": receipt_id,
                        "store_name": f"{retailer} Testmarkt",
                        "retailer": retailer,
                        "purchase_date": purchase_date,
                        "currency": currency,
                        "total": total,
                        "status": "analyzed",
                    },
                    [{"id": item_id, "raw_name": "TEST", "unit_price": 1.0}],
                )
                self.assertTrue(
                    local.update_catalog_item_mapping(
                        receipt_id, item_id, product["id"], True
                    )
                )
                self.assertTrue(local.record_catalog_purchase(receipt_id, item_id))

            add_confirmed("aug-rewe", "2026-08-03", 120.0, "REWE")
            add_confirmed("aug-dm", "2026-08-10", 80.0, "dm")
            add_confirmed("aug-missing", "2026-08-08", None, "REWE")
            add_confirmed("aug-usd", "2026-08-09", 20.0, "REWE", "USD")
            add_confirmed("jul-rewe", "2026-07-03", 100.0, "REWE")
            add_confirmed("jul-dm", "2026-07-10", 50.0, "dm")
            add_confirmed("jul-late", "2026-07-20", 300.0, "REWE")
            add_confirmed("jun", "2026-06-10", 90.0, "ALDI")
            local.create_receipt(
                {
                    "id": "aug-pending",
                    "store_name": "Noch zu prüfen",
                    "purchase_date": "2026-08-11",
                    "currency": "EUR",
                    "total": 999.0,
                    "status": "analyzed",
                },
                [{"id": "aug-pending-item", "raw_name": "OFFEN"}],
            )

            settings = local.set_budget_settings(
                household_id=owner["household_id"],
                user_id=owner["user_id"],
                monthly_limit=600,
                warning_percent=80,
            )
            self.assertTrue(settings["configured"])
            overview = local.budget_overview(
                owner["household_id"], months=3, today=datetime(2026, 8, 12).date()
            )
            current = overview["current_period"]
            self.assertEqual(current["spent"], 200.0)
            self.assertEqual(current["remaining"], 400.0)
            self.assertEqual(current["forecast"], 516.67)
            self.assertEqual(current["receipt_count"], 2)
            self.assertEqual(current["status"], "on_track")
            self.assertEqual(overview["comparison"]["spent"], 150.0)
            self.assertEqual(overview["comparison"]["change_amount"], 50.0)
            self.assertEqual(
                [month["spent"] for month in overview["months"]],
                [90.0, 450.0, 200.0],
            )
            self.assertEqual(
                [(store["store_key"], store["spent"]) for store in overview["stores"]],
                [("rewe", 120.0), ("dm", 80.0)],
            )
            self.assertEqual(
                overview["data_quality"],
                {
                    "confirmed_receipt_count": 4,
                    "counted_receipt_count": 2,
                    "pending_receipt_count": 1,
                    "missing_total_count": 1,
                    "other_currency_receipt_count": 1,
                    "coverage_percent": 50.0,
                },
            )
            reset = local.set_budget_settings(
                household_id=owner["household_id"],
                user_id=owner["user_id"],
                monthly_limit=None,
            )
            self.assertFalse(reset["configured"])

    def test_budget_api_is_authenticated_validated_and_audited(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/v1/insights/budget").status_code, 401)
            setup = client.post(
                "/api/v1/auth/setup",
                json={"password": "sicheres-budget-passwort", "display_name": "Owner Test"},
            )
            self.assertEqual(setup.status_code, 200)
            initial = client.get("/api/v1/insights/budget?months=6")
            self.assertEqual(initial.status_code, 200)
            self.assertFalse(initial.json()["settings"]["configured"])
            updated = client.put(
                "/api/v1/insights/budget/settings",
                json={"monthly_limit": 650, "warning_percent": 80},
            )
            self.assertEqual(updated.status_code, 200)
            self.assertEqual(updated.json()["monthly_limit"], 650.0)
            self.assertEqual(
                client.put(
                    "/api/v1/insights/budget/settings",
                    json={"monthly_limit": 0, "warning_percent": 80},
                ).status_code,
                422,
            )
            overview = client.get("/api/v1/insights/budget")
            self.assertEqual(overview.status_code, 200)
            self.assertTrue(overview.json()["settings"]["configured"])
            with database.connect() as conn:
                audit = conn.execute(
                    "SELECT action, details_json FROM audit_events WHERE category = 'budget' ORDER BY created_at DESC LIMIT 1"
                ).fetchone()
            self.assertEqual(audit["action"], "settings.update")
            audit_details = json.loads(audit["details_json"])
            self.assertEqual(
                set(audit_details),
                {"household_id", "configured", "warning_percent"},
            )
            self.assertTrue(audit_details["configured"])
            self.assertEqual(audit_details["warning_percent"], 80)

    def test_confirmed_scan_reconciles_open_receipt_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "reconcile.db")
            local.initialize()
            local.create_receipt(
                {"id": "receipt-1", "store_name": "REWE"},
                [
                    {
                        "id": "item-1",
                        "raw_name": "NEUES PRODUKT",
                        "normalized_name": "Neues Produkt",
                        "barcode": "4006381333931",
                    }
                ],
            )
            scan = local.create_scan(
                barcode_raw="4006381333931",
                barcode_normalized="4006381333931",
                symbology="EAN-13",
                mode="identify",
                resolution_source="unresolved",
            )
            local.ensure_scan_product(
                scan["id"],
                name="Neues Produkt",
                brand="Testmarke",
                image_url="https://images.example.test/product.png",
            )
            result = reconcile_unresolved_items(local)
            self.assertEqual(result["resolved"], 1)
            item = local.get_receipt("receipt-1")["items"][0]
            self.assertEqual(item["match_reason"], "barcode")
            self.assertEqual(item["match_evidence"][0]["label"], "Barcode stimmt exakt")
            self.assertEqual(item["catalog_variant_brand"], "Testmarke")
            self.assertEqual(
                item["catalog_product_image_url"],
                "https://images.example.test/product.png",
            )

    def test_barcode_normalization_validates_gtin_checksum(self) -> None:
        barcode = normalize_barcode(" 4006381333931 ")
        self.assertEqual(barcode.value, "4006381333931")
        self.assertEqual(barcode.symbology, "EAN-13")
        self.assertTrue(barcode.supports_open_facts_lookup)
        internal = normalize_barcode("12345")
        self.assertEqual(internal.symbology, "Interner Code")
        self.assertFalse(internal.supports_open_facts_lookup)
        with self.assertRaises(BarcodeValidationError):
            normalize_barcode("4006381333932")

    def test_scanner_actions_are_local_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "scanner.db")
            local.initialize()
            master = local.catalog_master_data()
            product = local.create_catalog_product(
                name="Testkaffee",
                location_id=master["locations"][0]["id"],
                quantity_unit_id=master["quantity_units"][0]["id"],
                brand="Testmarke",
                barcode="4000000000016",
            )
            resolved = local.create_scan(
                barcode_raw="4000000000016",
                barcode_normalized="4000000000016",
                symbology="EAN-13",
                mode="add",
                resolution_source="local",
                product_id=product["id"],
                variant_id=local.catalog_product_by_barcode("4000000000016")["variant_id"],
                resolve_key="resolve-scanner-test",
            )
            added = local.confirm_scan_action(
                resolved["id"],
                confirmation_key="confirm-scanner-add",
                quantity=2,
            )
            repeated = local.confirm_scan_action(
                resolved["id"],
                confirmation_key="confirm-scanner-add",
                quantity=2,
            )
            self.assertEqual(added["action_result"], repeated["action_result"])
            self.assertEqual(local.get_catalog_product(product["id"])["stock_quantity"], 2)

            consumed = local.create_scan(
                barcode_raw="4000000000016",
                barcode_normalized="4000000000016",
                symbology="EAN-13",
                mode="consume",
                resolution_source="local",
                product_id=product["id"],
                variant_id=resolved["variant_id"],
            )
            local.confirm_scan_action(
                consumed["id"],
                confirmation_key="confirm-scanner-consume",
                quantity=1,
            )
            self.assertEqual(local.get_catalog_product(product["id"])["stock_quantity"], 1)

            identified = local.create_scan(
                barcode_raw="4000000000016",
                barcode_normalized="4000000000016",
                symbology="EAN-13",
                mode="identify",
                resolution_source="local",
                product_id=product["id"],
                variant_id=resolved["variant_id"],
            )
            identified = local.confirm_scan_action(
                identified["id"],
                confirmation_key="confirm-scanner-identify",
                quantity=1,
            )
            self.assertEqual(identified["action_result"]["mode"], "identify")
            self.assertEqual(local.get_catalog_product(product["id"])["stock_quantity"], 1)

            opened = local.create_scan(
                barcode_raw="4000000000016",
                barcode_normalized="4000000000016",
                symbology="EAN-13",
                mode="open",
                resolution_source="local",
                product_id=product["id"],
                variant_id=resolved["variant_id"],
            )
            opened = local.confirm_scan_action(
                opened["id"],
                confirmation_key="confirm-scanner-open",
                quantity=1,
            )
            self.assertIn("opened_at", opened["action_result"])

            shopping = local.create_scan(
                barcode_raw="4000000000016",
                barcode_normalized="4000000000016",
                symbology="EAN-13",
                mode="shopping",
                resolution_source="local",
                product_id=product["id"],
                variant_id=resolved["variant_id"],
            )
            local.confirm_scan_action(
                shopping["id"],
                confirmation_key="confirm-scanner-shopping",
                quantity=2,
            )
            self.assertEqual(local.list_shopping_items()[0]["desired_quantity"], 2)

    def test_stock_count_is_transactional_idempotent_and_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "stock-count.db")
            local.initialize()
            master = local.catalog_master_data()
            first = local.create_catalog_product(
                name="Zählkaffee",
                location_id=master["locations"][0]["id"],
                quantity_unit_id=master["quantity_units"][0]["id"],
            )
            second = local.create_catalog_product(
                name="Zählmilch",
                location_id=master["locations"][1]["id"],
                quantity_unit_id=master["quantity_units"][0]["id"],
            )
            payload = [
                {"product_id": first["id"], "counted_quantity": 5},
                {"product_id": second["id"], "counted_quantity": 2},
            ]
            created = local.apply_stock_count(
                client_mutation_id="count-opening-test",
                source="manual",
                note="Erste Zählung",
                lines=payload,
            )
            repeated = local.apply_stock_count(
                client_mutation_id="count-opening-test",
                source="manual",
                note="Wird ignoriert",
                lines=payload,
            )
            self.assertEqual(created["id"], repeated["id"])
            self.assertEqual(created["changed_count"], 2)
            self.assertEqual(local.get_catalog_product(first["id"])["stock_quantity"], 5)
            self.assertEqual(local.get_catalog_product(second["id"])["stock_quantity"], 2)

            corrected = local.apply_stock_count(
                client_mutation_id="count-correction-test",
                source="manual",
                note="Kaffee korrigiert",
                lines=[
                    {"product_id": first["id"], "counted_quantity": 3},
                    {"product_id": second["id"], "counted_quantity": 2},
                ],
            )
            self.assertEqual(corrected["changed_count"], 1)
            self.assertEqual(local.get_catalog_product(first["id"])["stock_quantity"], 3)
            with local.connect() as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM stock_count_sessions").fetchone()[0], 2)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0], 3)
                self.assertEqual(
                    conn.execute(
                        "SELECT COUNT(*) FROM stock_movements WHERE movement_type = 'stock_count_decrease'"
                    ).fetchone()[0],
                    1,
                )

            with self.assertRaisesRegex(ValueError, "nur einmal"):
                local.apply_stock_count(
                    client_mutation_id="count-duplicate-lines",
                    source="manual",
                    note="",
                    lines=[
                        {"product_id": first["id"], "counted_quantity": 1},
                        {"product_id": first["id"], "counted_quantity": 2},
                    ],
                )
            with local.connect() as conn:
                self.assertEqual(
                    conn.execute(
                        "SELECT COUNT(*) FROM stock_count_sessions WHERE client_mutation_id = 'count-duplicate-lines'"
                    ).fetchone()[0],
                    0,
                )

    def test_low_stock_generation_is_reviewed_idempotent_and_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "shopping-list.db")
            local.initialize()
            master = local.catalog_master_data()
            product = local.create_catalog_product(
                name="Nachkauf Haferdrink",
                location_id=master["locations"][0]["id"],
                quantity_unit_id=master["quantity_units"][0]["id"],
                minimum_stock_quantity=2,
                shopping_target_quantity=6,
            )
            local.apply_stock_count(
                client_mutation_id="shopping-opening-count",
                source="manual",
                note="Ausgangsbestand",
                lines=[{"product_id": product["id"], "counted_quantity": 1}],
            )

            preview = local.low_stock_preview()
            self.assertEqual(len(preview), 1)
            self.assertEqual(preview[0]["current_quantity"], 1)
            self.assertEqual(preview[0]["suggested_quantity"], 5)
            self.assertIsNone(preview[0]["existing_item_id"])

            created = local.generate_shopping_list(
                client_mutation_id="shopping-generate-first",
                product_ids=[product["id"]],
            )
            repeated = local.generate_shopping_list(
                client_mutation_id="shopping-generate-first",
                product_ids=[product["id"]],
            )
            self.assertEqual(created["id"], repeated["id"])
            self.assertEqual(created["created_count"], 1)
            self.assertEqual(local.list_shopping_items()[0]["desired_quantity"], 5)

            unchanged = local.generate_shopping_list(
                client_mutation_id="shopping-generate-second",
                product_ids=[product["id"]],
            )
            self.assertEqual(unchanged["unchanged_count"], 1)
            self.assertEqual(len(local.list_shopping_items()), 1)

            item = local.list_shopping_items()[0]
            edited = local.update_shopping_item(
                item["id"],
                desired_quantity=4,
                checked=False,
                notes="Eine Packung ist noch unterwegs",
                expected_updated_at=item["updated_at"],
            )
            self.assertEqual(edited["desired_quantity"], 4)
            completed = local.update_shopping_item(
                item["id"],
                desired_quantity=4,
                checked=True,
                notes=edited["notes"],
                expected_updated_at=edited["updated_at"],
            )
            self.assertEqual(completed["checked"], 1)
            self.assertEqual(local.list_shopping_items(), [])

            local.apply_stock_count(
                client_mutation_id="shopping-recovered-count",
                source="manual",
                note="Bestand aufgefüllt",
                lines=[{"product_id": product["id"], "counted_quantity": 6}],
            )
            self.assertEqual(local.low_stock_preview(), [])
            skipped = local.generate_shopping_list(
                client_mutation_id="shopping-generate-stale-review",
                product_ids=[product["id"]],
            )
            self.assertEqual(skipped["skipped_count"], 1)
            self.assertEqual(local.list_shopping_items(), [])

    def test_unknown_scan_is_reused_and_can_be_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "unknown.db")
            local.initialize()
            first = local.create_scan(
                barcode_raw="12345",
                barcode_normalized="12345",
                symbology="GS1/Code",
                mode="identify",
                resolution_source="unresolved",
                suggestion={"name": "Vorschlag"},
            )
            repeated = local.create_scan(
                barcode_raw="12345",
                barcode_normalized="12345",
                symbology="GS1/Code",
                mode="identify",
                resolution_source="unresolved",
            )
            self.assertEqual(first["id"], repeated["id"])
            mapped = local.ensure_scan_product(
                first["id"], name="Neues Testprodukt", brand="Testmarke"
            )
            self.assertEqual(mapped["status"], "resolved")
            self.assertEqual(
                local.catalog_product_by_barcode("12345")["id"], mapped["product_id"]
            )

    def test_versioned_scanner_api_resolves_and_confirms_once(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/api/v1/auth/setup", json={"password": "sicheres-test-passwort"}
            )
            master = database.catalog_master_data()
            product = database.create_catalog_product(
                name="API Testkaffee",
                location_id=master["locations"][0]["id"],
                quantity_unit_id=master["quantity_units"][0]["id"],
                barcode="4006381333931",
            )
            resolved = client.post(
                "/api/v1/scans/resolve",
                json={
                    "barcode": "4006381333931",
                    "mode": "add",
                    "client_mutation_id": "resolve-api-scanner-test",
                },
            )
            self.assertEqual(resolved.status_code, 200)
            self.assertEqual(resolved.json()["product_id"], product["id"])
            scan_id = resolved.json()["id"]
            confirmation = {
                "client_mutation_id": "confirm-api-scanner-test",
                "quantity": 2,
            }
            first = client.post(
                f"/api/v1/scans/{scan_id}/confirm", json=confirmation
            )
            repeated = client.post(
                f"/api/v1/scans/{scan_id}/confirm", json=confirmation
            )
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.json()["status"], "confirmed")
            self.assertEqual(first.json()["action_result"], repeated.json()["action_result"])
            self.assertEqual(database.get_catalog_product(product["id"])["stock_quantity"], 2)

    def test_versioned_scanner_api_keeps_unknown_code_in_inbox(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/api/v1/auth/setup", json={"password": "sicheres-test-passwort"}
            )
            with patch(
                "app.main.lookup_open_facts", new=AsyncMock(return_value=None)
            ) as external_lookup:
                response = client.post(
                    "/api/v1/scans/resolve",
                    json={
                        "barcode": "12345",
                        "mode": "identify",
                        "client_mutation_id": "resolve-unknown-api-test",
                    },
                )
            external_lookup.assert_not_awaited()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "unresolved")
            self.assertEqual(response.json()["symbology"], "Interner Code")
            inbox = client.get("/api/v1/scans/unresolved")
            self.assertEqual(inbox.status_code, 200)
            self.assertEqual(inbox.json()[0]["id"], response.json()["id"])

    def test_candidate_api_requires_review_and_learns_confirmed_product(self) -> None:
        with TestClient(app) as client:
            client.post(
                "/api/v1/auth/setup", json={"password": "sicheres-test-passwort"}
            )
            database.create_receipt(
                {"id": "candidate-receipt", "store_name": "REWE", "currency": "EUR"},
                [
                    {
                        "id": "candidate-item",
                        "raw_name": "HAFERDRINK BARISTA",
                        "normalized_name": "Haferdrink Barista",
                        "unit_price": 2.49,
                    }
                ],
            )
            candidate_response = {
                "query": "Haferdrink Barista",
                "store_name": "REWE",
                "receipt_unit_price": 2.49,
                "currency": "EUR",
                "source": "open_facts",
                "cached": False,
                "ai_ranked": True,
                "candidates": [
                    {
                        "external_id": "9876543210123",
                        "barcode": "9876543210123",
                        "name": "Haferdrink Barista API",
                        "brand": "Testmarke",
                        "quantity": "1 l",
                        "image_url": "https://images.example.test/candidate.jpg",
                        "stores": ["REWE"],
                        "source": "open_facts",
                        "source_label": "Open Facts",
                        "source_url": "https://world.openfoodfacts.org/product/9876543210123",
                        "database_license": "ODbL-1.0",
                        "image_license": "CC-BY-SA",
                        "attribution": "Open Food Facts contributors",
                        "score": 96,
                        "ai_confidence": 94,
                        "ai_reason": "Name, Händler und Packungsmenge passen",
                        "store_match": True,
                        "local_product_id": None,
                        "local_product_name": None,
                        "evidence": [{"source": "store", "label": "Bei REWE gelistet"}],
                    }
                ],
                "warnings": [],
            }
            with patch(
                "app.main.find_product_candidates",
                new=AsyncMock(return_value=candidate_response),
            ):
                suggestions = client.get(
                    "/api/v1/receipts/candidate-receipt/items/candidate-item/candidates"
                )
            self.assertEqual(suggestions.status_code, 200)
            self.assertEqual(suggestions.json()["candidates"][0]["score"], 96)
            database.put_external_product(
                "open_facts",
                "9876543210123",
                {
                    "barcode": "9876543210123",
                    "name": "Haferdrink Barista API",
                    "brand": "Testmarke",
                    "quantity": "1 l",
                    "image_url": "https://images.example.test/candidate.jpg",
                    "source_url": "https://world.openfoodfacts.org/product/9876543210123",
                    "database_license": "ODbL-1.0",
                    "attribution": "Open Food Facts contributors",
                },
            )
            master = database.catalog_master_data()
            confirmed = client.post(
                "/api/v1/receipts/candidate-receipt/items/candidate-item/candidate",
                json={
                    "source": "open_facts",
                    "external_id": "9876543210123",
                    "name": "Haferdrink Barista API",
                    "location_id": master["locations"][0]["id"],
                    "quantity_unit_id": master["quantity_units"][0]["id"],
                    "default_best_before_days": 30,
                    "remember": True,
                },
            )
            self.assertEqual(confirmed.status_code, 200)
            item = confirmed.json()["items"][0]
            self.assertEqual(item["catalog_variant_brand"], "Testmarke")
            self.assertEqual(
                item["catalog_product_image_url"],
                "https://images.example.test/candidate.jpg",
            )

    def test_grocy_catalog_import_is_additive_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "migration.db")
            local.initialize()
            master = {
                "locations": [{"id": 9, "name": "Speisekammer", "active": 1}],
                "quantity_units": [{"id": 8, "name": "Karton", "active": 1}],
                "product_groups": [{"id": 7, "name": "Getränke", "active": 1}],
            }
            products = [
                {
                    "id": 42,
                    "name": "Mineralwasser",
                    "active": 1,
                    "location_id": 9,
                    "qu_id_stock": 8,
                    "product_group_id": 7,
                    "default_best_before_days": 365,
                }
            ]
            local.import_grocy_catalog(master, products)
            local.import_grocy_catalog(master, products)
            matches = [
                product
                for product in local.list_catalog_products("Mineralwasser")
                if product["grocy_product_id"] == 42
            ]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["default_location_name"], "Speisekammer")
            self.assertEqual(matches[0]["default_quantity_unit_name"], "Karton")

    def test_grocy_stock_preview_aggregates_lots_without_writing_stock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "grocy-preview.db")
            local.initialize()
            master = {
                "locations": [{"id": 9, "name": "Speisekammer", "active": 1}],
                "quantity_units": [{"id": 8, "name": "Packung", "active": 1}],
                "product_groups": [],
            }
            local.import_grocy_catalog(
                master,
                [
                    {
                        "id": 42,
                        "name": "Vorschau Kaffee",
                        "active": 1,
                        "location_id": 9,
                        "qu_id_stock": 8,
                    }
                ],
            )
            preview = local.grocy_stock_preview(
                [
                    {"product_id": 42, "amount": "2", "best_before_date": "2027-02-01"},
                    {"product_id": 42, "amount": "1", "best_before_date": "2027-01-01"},
                    {"product_id": 99, "amount": "4", "product_name": "Nicht importiert"},
                ]
            )
            self.assertEqual(preview["items"][0]["proposed_quantity"], 3)
            self.assertEqual(preview["items"][0]["quantity_delta"], 3)
            self.assertEqual(preview["items"][0]["best_before_date"], "2027-01-01")
            self.assertEqual(preview["unmapped"][0]["grocy_product_id"], 99)
            self.assertEqual(local.catalog_summary()["stock_lots"], 0)

    def test_openapi_contract_is_versioned_and_scoped_token_authenticated(self) -> None:
        schema = app.openapi()
        self.assertEqual(schema["openapi"], "3.1.0")
        self.assertEqual(schema["info"]["version"], "0.8.23")
        self.assertIn("/api/v1/privacy/export", schema["paths"])
        self.assertIn("/api/v1/operations/overview", schema["paths"])
        self.assertIn("/api/v1/catalog/products", schema["paths"])
        self.assertIn("/api/v1/scans/resolve", schema["paths"])
        self.assertIn("/api/v1/scans/{scan_id}/confirm", schema["paths"])
        self.assertIn("/api/v1/catalog/reconcile", schema["paths"])
        self.assertIn(
            "/api/v1/receipts/{receipt_id}/items/{item_id}/candidates",
            schema["paths"],
        )
        self.assertIn(
            "/api/v1/receipts/{receipt_id}/items/{item_id}/candidate",
            schema["paths"],
        )
        self.assertIn(
            "/api/v1/catalog/products/{product_id}/price-history", schema["paths"]
        )
        self.assertIn("/api/v1/insights/prices", schema["paths"])
        self.assertIn("/api/v1/insights/budget", schema["paths"])
        self.assertIn("/api/v1/insights/budget/settings", schema["paths"])
        self.assertIn("/api/v1/catalog/products/{product_id}", schema["paths"])
        self.assertIn("/api/v1/catalog/products/{product_id}/image", schema["paths"])
        self.assertIn(
            "/api/v1/catalog/products/{product_id}/variants", schema["paths"]
        )
        self.assertIn("/api/v1/catalog/variants/{variant_id}", schema["paths"])
        self.assertIn(
            "/api/v1/catalog/variants/{variant_id}/barcodes", schema["paths"]
        )
        self.assertIn(
            "/api/v1/catalog/master-data/{kind}/{item_id}", schema["paths"]
        )
        self.assertIn("/api/v1/stock/count/products", schema["paths"])
        self.assertIn("/api/v1/stock/counts", schema["paths"])
        self.assertIn("/api/v1/shopping-list", schema["paths"])
        self.assertIn("/api/v1/shopping-list/low-stock", schema["paths"])
        self.assertIn("/api/v1/shopping-list/generate", schema["paths"])
        self.assertIn("/api/v1/shopping-list/{item_id}", schema["paths"])
        self.assertIn("/api/v1/integrations/grocy/stock-preview", schema["paths"])
        self.assertIn("/api/v1/auth/api-tokens", schema["paths"])
        self.assertIn("/api/v1/notifications/state", schema["paths"])
        self.assertIn("/api/v1/notifications/preferences", schema["paths"])
        self.assertIn("/api/v1/notifications/subscriptions", schema["paths"])
        self.assertIn("/api/v1/notifications/test", schema["paths"])
        self.assertNotIn("/api/catalog/products", schema["paths"])
        security = schema["components"]["securitySchemes"]["householdSession"]
        bearer = schema["components"]["securitySchemes"]["apiToken"]
        self.assertEqual(security["in"], "cookie")
        self.assertEqual(bearer["scheme"], "bearer")
        self.assertEqual(
            schema["paths"]["/api/v1/catalog/products"]["get"]["security"],
            [{"householdSession": []}, {"apiToken": []}],
        )
        self.assertEqual(
            schema["paths"]["/api/v1/catalog/products"]["get"]["x-vorrio-required-scope"],
            "catalog:read",
        )
        self.assertEqual(
            schema["paths"]["/api/v1/settings"]["get"]["security"],
            [{"householdSession": []}],
        )
        self.assertIn("/api/readiness", schema["paths"])
        self.assertNotIn(
            "security", schema["paths"]["/api/readiness"]["get"]
        )
        self.assertIn("Signed HttpOnly", security["description"])

    def test_security_headers_origin_guard_and_trusted_hosts(self) -> None:
        with TestClient(app) as client:
            health = client.get("/api/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.headers["x-content-type-options"], "nosniff")
            self.assertEqual(health.headers["x-frame-options"], "DENY")
            self.assertEqual(health.headers["cross-origin-opener-policy"], "same-origin")
            self.assertIn("default-src 'self'", health.headers["content-security-policy"])

            api_state = client.get("/api/v1/auth/state")
            self.assertEqual(api_state.headers["cache-control"], "no-store")

            rejected_host = client.get(
                "/api/health", headers={"Host": "unexpected.example"}
            )
            self.assertEqual(rejected_host.status_code, 400)

            rejected_origin = client.post(
                "/api/v1/auth/setup",
                headers={"Origin": "https://attacker.example"},
                json={"password": "sicheres-test-passwort"},
            )
            self.assertEqual(rejected_origin.status_code, 403)
            self.assertTrue(client.get("/api/v1/auth/state").json()["needs_setup"])

    def test_public_profile_contract_and_runtime_gate_fail_closed(self) -> None:
        safe_public = replace(
            config,
            deployment_profile="public_https",
            public_url="https://vorrio.example.com",
            trusted_hosts=("vorrio.example.com",),
            allowed_origins=("https://vorrio.example.com",),
            forwarded_allow_ips="172.20.0.0/16",
            session_https_only=True,
            public_exposure_acknowledged=True,
        )
        self.assertEqual(public_exposure_failures(safe_public), ())
        self.assertIn(
            "acknowledgement_missing",
            public_exposure_failures(
                replace(
                    safe_public,
                    public_exposure_acknowledged=False,
                    trusted_hosts=("*",),
                )
            ),
        )
        self.assertIn(
            "canonical_origin_not_allowed",
            public_exposure_failures(
                replace(safe_public, allowed_origins=("https://other.example.com",))
            ),
        )
        self.assertIn(
            "forwarded_proxy_unrestricted",
            public_exposure_failures(
                replace(safe_public, forwarded_allow_ips="0.0.0.0/0")
            ),
        )
        self.assertIn(
            "forwarded_proxy_invalid",
            public_exposure_failures(
                replace(safe_public, forwarded_allow_ips="proxy.example.com")
            ),
        )

        gated = FastAPI()

        @gated.get("/")
        async def gated_home() -> dict[str, bool]:
            return {"ok": True}

        gated.add_middleware(
            PublicExposureGateMiddleware,
            blocked_reasons=("acknowledgement_missing",),
        )
        with TestClient(gated) as client:
            response = client.get("/")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_outbound_url_contract_blocks_credential_and_special_targets(self) -> None:
        self.assertEqual(
            normalize_connector_url("http://host.docker.internal:11434/v1/"),
            "http://host.docker.internal:11434/v1",
        )
        self.assertEqual(
            normalize_connector_url(
                "https://api.openai.com/v1", require_https=True
            ),
            "https://api.openai.com/v1",
        )
        with self.assertRaises(OutboundUrlError):
            normalize_connector_url("https://user:secret@example.com/v1")
        with self.assertRaises(OutboundUrlError):
            normalize_connector_url("http://169.254.169.254/latest/meta-data")
        with self.assertRaises(OutboundUrlError):
            normalize_connector_url("http://api.example.com/v1", require_https=True)
        with self.assertRaises(OutboundUrlError):
            validate_public_push_url("https://192.168.1.10/push")
        with self.assertRaises(OutboundUrlError):
            validate_public_push_url("https://push.local/subscription")

    def test_provider_http_errors_never_expose_remote_response_bodies(self) -> None:
        unauthorized = str(_provider_http_error("KI-Anbieter", 401))
        throttled = str(_provider_http_error("Anthropic", 429))
        failed = str(_provider_http_error("KI-Anbieter", 503))

        self.assertIn("API-Key", unauthorized)
        self.assertIn("Anfragelimit", throttled)
        self.assertIn("vorübergehend", failed)
        self.assertNotIn("response", unauthorized.lower())
        self.assertNotIn("bearer", unauthorized.lower())

    def test_request_body_limit_rejects_before_json_parsing(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login",
                headers={"Content-Length": str(config.max_request_bytes + 1)},
                content=b"{}",
            )
            self.assertEqual(response.status_code, 413)

    def test_image_validation_rejects_mismatched_or_invalid_content(self) -> None:
        with self.assertRaisesRegex(MediaValidationError, "ungültig|passen"):
            validate_image_upload(b"not-an-image" * 20, "image/jpeg", 40_000_000)

    def test_secret_rotation_backs_up_and_reencrypts_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.db"
            local = Database(path)
            local.initialize()
            old_secret = "old-synthetic-secret-0123456789abcdef"
            new_secret = "new-synthetic-secret-0123456789abcdef"
            stored = {"provider": {"api_key": "synthetic-provider-key"}}
            local.put_setting(
                "connections.v1", SecretStore(old_secret).encrypt_json(stored)
            )
            vapid = {"private_key": "private-vapid-test", "public_key": "public-vapid-test"}
            local.put_setting(
                "notifications.webpush.v1",
                SecretStore(old_secret).encrypt_json(vapid),
            )

            backup_path = rotate_secret(path, old_secret, new_secret)

            self.assertTrue(backup_path.is_file())
            encrypted = local.get_setting("connections.v1")
            self.assertEqual(
                SecretStore(new_secret).decrypt_json(encrypted), stored
            )
            self.assertEqual(
                SecretStore(new_secret).decrypt_json(
                    local.get_setting("notifications.webpush.v1")
                ),
                vapid,
            )
            with self.assertRaisesRegex(RuntimeError, "nicht entschlüsselt"):
                SecretStore(old_secret).decrypt_json(encrypted)
            self.assertEqual(
                local.list_audit_events(1)[0]["action"], "app_secret_rotation"
            )

    def test_readiness_reports_safe_test_configuration(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/readiness")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["status"], "ready")
            self.assertEqual(payload["profile"], "lan")
            self.assertTrue(all(check["status"] == "pass" for check in payload["checks"]))

    def test_public_example_secrets_are_never_considered_safe(self) -> None:
        self.assertFalse(is_safe_secret_key("development-change-me"))
        self.assertFalse(
            is_safe_secret_key("replace-with-at-least-32-random-characters")
        )
        self.assertFalse(is_safe_secret_key("short"))
        self.assertTrue(is_safe_secret_key("a-unique-test-secret-with-32-characters"))

    def test_catalog_editor_api_updates_product_variant_barcode_and_master_data(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(
                client.post(
                    "/api/v1/auth/setup", json={"password": "sicheres-test-passwort"}
                ).status_code,
                200,
            )
            master = database.catalog_master_data()
            created_product = client.post(
                "/api/v1/catalog/products",
                json={
                    "name": "Editor API Haferdrink",
                    "location_id": master["locations"][0]["id"],
                    "quantity_unit_id": master["quantity_units"][0]["id"],
                },
            )
            self.assertEqual(created_product.status_code, 200)
            product = created_product.json()
            detail = client.get(f"/api/v1/catalog/products/{product['id']}")
            self.assertEqual(detail.status_code, 200)

            update_payload = {
                "name": "Editor API Haferdrink Barista",
                "product_group_id": master["product_groups"][0]["id"],
                "default_location_id": master["locations"][0]["id"],
                "default_quantity_unit_id": master["quantity_units"][0]["id"],
                "default_best_before_days": 180,
                "image_url": "https://images.example.test/editor-product.jpg",
                "notes": "Familienfavorit",
                "expected_updated_at": detail.json()["updated_at"],
            }
            updated = client.patch(
                f"/api/v1/catalog/products/{product['id']}", json=update_payload
            )
            self.assertEqual(updated.status_code, 200)
            self.assertEqual(updated.json()["notes"], "Familienfavorit")
            self.assertEqual(
                client.patch(
                    f"/api/v1/catalog/products/{product['id']}", json=update_payload
                ).status_code,
                409,
            )

            variant = client.post(
                f"/api/v1/catalog/products/{product['id']}/variants",
                json={
                    "name": "Barista",
                    "brand": "Vorrio Test",
                    "package_amount": 1,
                    "package_unit": "l",
                    "image_url": None,
                },
            )
            self.assertEqual(variant.status_code, 200)
            variant_id = variant.json()["variants"][0]["id"]
            barcode = client.post(
                f"/api/v1/catalog/variants/{variant_id}/barcodes",
                json={"barcode": "4311596654574"},
            )
            self.assertEqual(barcode.status_code, 200)
            self.assertEqual(
                barcode.json()["variants"][0]["barcodes"][0]["symbology"],
                "EAN-13",
            )

            created_master = client.post(
                "/api/v1/catalog/master-data/locations",
                json={
                    "name": "Editor API Abstellraum",
                    "description": "Testlager",
                    "is_freezer": False,
                    "name_plural": None,
                },
            )
            self.assertEqual(created_master.status_code, 200)
            master_id = created_master.json()["id"]
            renamed_master = client.patch(
                f"/api/v1/catalog/master-data/locations/{master_id}",
                json={
                    "name": "Editor API Vorratsraum",
                    "description": "Umbenannt",
                    "is_freezer": False,
                    "name_plural": None,
                    "expected_updated_at": created_master.json()["updated_at"],
                },
            )
            self.assertEqual(renamed_master.status_code, 200)
            self.assertEqual(
                client.delete(
                    f"/api/v1/catalog/master-data/locations/{master_id}"
                ).status_code,
                200,
            )
            actions = {event["action"] for event in database.list_audit_events(20)}
            self.assertIn("product.create", actions)
            self.assertIn("product.update", actions)
            self.assertIn("variant.create", actions)
            self.assertIn("barcode.create", actions)
            self.assertIn("master_data.archive", actions)

    def test_private_product_image_upload_export_and_delete(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(
                client.post(
                    "/api/v1/auth/setup", json={"password": "sicheres-test-passwort"}
                ).status_code,
                200,
            )
            master = database.catalog_master_data()
            product = client.post(
                "/api/v1/catalog/products",
                json={
                    "name": "Produktbild Test",
                    "location_id": master["locations"][0]["id"],
                    "quantity_unit_id": master["quantity_units"][0]["id"],
                },
            ).json()

            raw = io.BytesIO()
            exif = Image.Exif()
            exif[0x010E] = "private camera note"
            Image.new("RGB", (1800, 1200), color=(34, 111, 67)).save(
                raw, format="JPEG", quality=90, exif=exif
            )
            uploaded = client.post(
                f"/api/v1/catalog/products/{product['id']}/image",
                files={"image": ("produkt.jpg", raw.getvalue(), "image/jpeg")},
            )
            self.assertEqual(uploaded.status_code, 200)
            detail = uploaded.json()
            self.assertEqual(
                detail["image_url"],
                f"/api/v1/catalog/products/{product['id']}/image",
            )
            image_response = client.get(detail["image_url"])
            self.assertEqual(image_response.status_code, 200)
            self.assertEqual(image_response.headers["content-type"], "image/webp")
            self.assertEqual(image_response.headers["cache-control"], "private, no-cache")
            with Image.open(io.BytesIO(image_response.content)) as stored:
                self.assertEqual(stored.format, "WEBP")
                self.assertLessEqual(max(stored.size), 1600)
                self.assertFalse(stored.getexif())

            preview = client.get("/api/v1/privacy/export/preview").json()
            self.assertEqual(preview["product_image_file_count"], 1)
            exported = client.get(
                "/api/v1/privacy/export?include_receipt_files=false"
            )
            self.assertEqual(exported.status_code, 200)
            with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
                self.assertIn(
                    f"product-images/{product['id']}.webp", archive.namelist()
                )
                manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(manifest["product_images_included"], 1)

            bad_internal = client.patch(
                f"/api/v1/catalog/products/{product['id']}",
                json={
                    "name": detail["name"],
                    "product_group_id": detail["product_group_id"],
                    "default_location_id": detail["default_location_id"],
                    "default_quantity_unit_id": detail["default_quantity_unit_id"],
                    "default_best_before_days": detail["default_best_before_days"],
                    "minimum_stock_quantity": detail["minimum_stock_quantity"],
                    "shopping_target_quantity": detail["shopping_target_quantity"],
                    "image_url": "/api/v1/catalog/products/00000000-0000-0000-0000-000000000000/image",
                    "notes": detail["notes"],
                    "expected_updated_at": detail["updated_at"],
                },
            )
            self.assertEqual(bad_internal.status_code, 422)

            deleted = client.delete(
                f"/api/v1/catalog/products/{product['id']}/image"
            )
            self.assertEqual(deleted.status_code, 200)
            self.assertIsNone(deleted.json()["image_url"])
            self.assertEqual(client.get(detail["image_url"]).status_code, 404)
            rejected = client.post(
                f"/api/v1/catalog/products/{product['id']}/image",
                files={"image": ("produkt.svg", b"<svg></svg>", "image/svg+xml")},
            )
            self.assertEqual(rejected.status_code, 422)

    def test_stock_count_api_requires_review_and_is_idempotent(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(
                client.post(
                    "/api/v1/auth/setup", json={"password": "sicheres-test-passwort"}
                ).status_code,
                200,
            )
            master = database.catalog_master_data()
            product = client.post(
                "/api/v1/catalog/products",
                json={
                    "name": "API Anfangsbestand Kakao",
                    "location_id": master["locations"][0]["id"],
                    "quantity_unit_id": master["quantity_units"][0]["id"],
                },
            ).json()
            payload = {
                "client_mutation_id": "count-api-opening-stock",
                "source": "manual",
                "note": "Küchenschrank gezählt",
                "lines": [
                    {
                        "product_id": product["id"],
                        "location_id": master["locations"][0]["id"],
                        "counted_quantity": 4,
                        "best_before_date": "2027-01-31",
                    }
                ],
            }
            created = client.post("/api/v1/stock/counts", json=payload)
            self.assertEqual(created.status_code, 200)
            self.assertEqual(created.json()["changed_count"], 1)
            repeated = client.post("/api/v1/stock/counts", json=payload)
            self.assertEqual(repeated.status_code, 200)
            self.assertEqual(repeated.json()["id"], created.json()["id"])
            products = client.get("/api/v1/stock/count/products").json()
            counted = next(row for row in products if row["id"] == product["id"])
            self.assertEqual(counted["stock_quantity"], 4)
            sessions = client.get("/api/v1/stock/counts").json()
            self.assertEqual(sessions[0]["lines"][0]["product_name"], "API Anfangsbestand Kakao")
            self.assertIn(
                "count.confirm",
                {event["action"] for event in database.list_audit_events(20)},
            )

    def test_shopping_list_api_reviews_generates_and_completes_low_stock(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(
                client.post(
                    "/api/v1/auth/setup", json={"password": "sicheres-test-passwort"}
                ).status_code,
                200,
            )
            master = database.catalog_master_data()
            product_response = client.post(
                "/api/v1/catalog/products",
                json={
                    "name": "API Nachkauf Penne",
                    "location_id": master["locations"][0]["id"],
                    "quantity_unit_id": master["quantity_units"][0]["id"],
                    "minimum_stock_quantity": 1,
                    "shopping_target_quantity": 4,
                },
            )
            self.assertEqual(product_response.status_code, 200)
            product = product_response.json()
            count = client.post(
                "/api/v1/stock/counts",
                json={
                    "client_mutation_id": "shopping-api-opening-count",
                    "source": "manual",
                    "note": "Startbestand",
                    "lines": [
                        {"product_id": product["id"], "counted_quantity": 1}
                    ],
                },
            )
            self.assertEqual(count.status_code, 200)

            preview = client.get("/api/v1/shopping-list/low-stock")
            self.assertEqual(preview.status_code, 200)
            candidate = next(
                item
                for item in preview.json()["items"]
                if item["product_id"] == product["id"]
            )
            self.assertEqual(candidate["suggested_quantity"], 3)

            payload = {
                "client_mutation_id": "shopping-api-generate",
                "product_ids": [product["id"]],
            }
            generated = client.post("/api/v1/shopping-list/generate", json=payload)
            self.assertEqual(generated.status_code, 200)
            self.assertEqual(generated.json()["created_count"], 1)
            repeated = client.post("/api/v1/shopping-list/generate", json=payload)
            self.assertEqual(repeated.json()["id"], generated.json()["id"])

            shopping = client.get("/api/v1/shopping-list")
            item = next(
                row for row in shopping.json() if row["product_id"] == product["id"]
            )
            self.assertEqual(item["desired_quantity"], 3)
            completed = client.patch(
                f"/api/v1/shopping-list/{item['id']}",
                json={
                    "desired_quantity": item["desired_quantity"],
                    "checked": True,
                    "notes": "Im Wagen",
                    "expected_updated_at": item["updated_at"],
                },
            )
            self.assertEqual(completed.status_code, 200)
            self.assertTrue(completed.json()["checked"])
            self.assertNotIn(
                product["id"],
                {row["product_id"] for row in client.get("/api/v1/shopping-list").json()},
            )
            actions = {event["action"] for event in database.list_audit_events(30)}
            self.assertIn("minimum.generate", actions)
            self.assertIn("item.complete", actions)

            invalid_rule = client.post(
                "/api/v1/catalog/products",
                json={
                    "name": "API Ungültiger Nachkauf",
                    "minimum_stock_quantity": 3,
                    "shopping_target_quantity": 3,
                },
            )
            self.assertEqual(invalid_rule.status_code, 422)

    def test_login_rate_limit_and_authentication_audit(self) -> None:
        with TestClient(app) as client:
            setup = client.post(
                "/api/v1/auth/setup", json={"password": "sicheres-test-passwort"}
            )
            self.assertEqual(setup.status_code, 200)
            client.post("/api/v1/auth/logout")

            for _ in range(5):
                response = client.post(
                    "/api/v1/auth/login", json={"password": "falsch-falsch"}
                )
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["detail"], "Anmeldung nicht möglich")

            blocked = client.post(
                "/api/v1/auth/login", json={"password": "sicheres-test-passwort"}
            )
            self.assertEqual(blocked.status_code, 429)
            self.assertIn("Retry-After", blocked.headers)

            events = database.list_audit_events(20)
            outcomes = {event["outcome"] for event in events}
            self.assertIn("success", outcomes)
            self.assertIn("failure", outcomes)
            self.assertIn("blocked", outcomes)
            self.assertTrue(all(event["source_hash"] != "testclient" for event in events))

    def test_unconfirmed_legacy_fuzzy_match_is_demoted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "migration.db")
            local.initialize()
            local.create_receipt(
                {"id": "receipt-1", "store_name": "REWE"},
                [
                    {
                        "id": "item-1",
                        "raw_name": "SALAMISTICKS",
                        "grocy_product_id": 11,
                        "grocy_product_name": "Salami",
                        "match_status": "fuzzy",
                        "match_score": 90,
                    }
                ],
            )
            local.initialize()
            item = local.get_receipt("receipt-1")["items"][0]
            self.assertIsNone(item["grocy_product_id"])
            self.assertEqual(item["suggested_product_id"], 11)
            self.assertEqual(item["match_status"], "suggested")

    def test_conflicting_global_alias_stays_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "conflicts.db")
            local.initialize()
            for index, product_id in enumerate((7, 8), start=1):
                local.create_receipt(
                    {"id": f"receipt-{index}", "store_name": "REWE"},
                    [
                        {
                            "id": f"item-{index}",
                            "raw_name": "HAUSMARKE MILCH",
                            "normalized_name": "Milch",
                        }
                    ],
                )
                local.update_item_mapping(
                    f"receipt-{index}",
                    f"item-{index}",
                    product_id,
                    f"Milch {product_id}",
                    True,
                )
            self.assertIsNone(local.get_alias("HAUSMARKE MILCH", "Milch"))

    def test_invalid_pdf_is_rejected_before_provider_call(self) -> None:
        with self.assertRaisesRegex(PdfReceiptError, "kein gültiges PDF"):
            prepare_pdf_receipt(b"not-a-pdf" * 20)

    def test_analysis_prompt_contains_existing_master_data_and_missing_rule(self) -> None:
        prompt = build_analysis_prompt(
            {
                "locations": [
                    {"id": 1, "name": "Vorratskammer", "active": 1},
                    {"id": 2, "name": "Tiefkühler", "active": 1},
                ],
                "quantity_units": [{"id": 1, "name": "Packung", "active": 1}],
                "product_groups": [
                    {"id": 1, "name": "Tiefkühlprodukte", "active": 1}
                ],
            }
        )
        self.assertIn("Tiefkühler", prompt)
        self.assertIn("Tiefkühlprodukte", prompt)
        self.assertIn("Wenn keiner passt", prompt)

    def test_existing_users_receive_release_notes_while_later_users_receive_onboarding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "experience-migration.db")
            local.initialize()
            with local.connect() as conn:
                conn.execute(
                    "DELETE FROM app_settings WHERE key = 'migration.user_experience_0_8_19'"
                )
            existing = local.ensure_owner_identity(hash_password("existing-password"))

            local.initialize()

            migrated = local.get_user_experience(str(existing["user_id"]))
            self.assertIsNotNone(migrated["onboarding_completed_at"])
            self.assertEqual(migrated["last_acknowledged_version"], "0.8.18")

            later_user_id = "later-user"
            timestamp = now_iso()
            with local.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO users(
                        id, display_name, password_hash, owner_setup_complete,
                        created_at, updated_at
                    ) VALUES (?, 'Later User', ?, 1, ?, ?)
                    """,
                    (
                        later_user_id,
                        hash_password("later-password"),
                        timestamp,
                        timestamp,
                    ),
                )
            later = local.get_user_experience(later_user_id)
            self.assertIsNone(later["onboarding_completed_at"])
            self.assertIsNone(later["last_acknowledged_version"])


class GrocyClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_catalog_editor_preserves_aliases_and_protects_used_master_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "catalog-editor.db")
            local.initialize()
            master = local.catalog_master_data()
            location = local.create_catalog_master_data(
                "locations",
                name="Nebenkammer",
                description="Zusätzlicher Vorrat",
                is_freezer=False,
                name_plural=None,
            )
            product = local.create_catalog_product(
                name="Testkaffee Classic",
                location_id=location["id"],
                quantity_unit_id=master["quantity_units"][0]["id"],
            )
            detail = local.get_catalog_product_detail(product["id"])
            updated = local.update_catalog_product(
                product["id"],
                name="Testkaffee Crema",
                product_group_id=master["product_groups"][0]["id"],
                default_location_id=location["id"],
                default_quantity_unit_id=master["quantity_units"][0]["id"],
                default_best_before_days=365,
                minimum_stock_quantity=1,
                shopping_target_quantity=4,
                image_url=None,
                notes="Testnotiz",
                expected_updated_at=detail["updated_at"],
            )
            with local.connect() as conn:
                alias = conn.execute(
                    "SELECT product_id FROM catalog_aliases WHERE alias_key = ?",
                    (normalize_key("Testkaffee Classic"),),
                ).fetchone()
            self.assertEqual(alias["product_id"], product["id"])
            with self.assertRaisesRegex(RuntimeError, "inzwischen geändert"):
                local.update_catalog_product(
                    product["id"],
                    name="Veralteter Schreibversuch",
                    product_group_id=None,
                    default_location_id=None,
                    default_quantity_unit_id=None,
                    default_best_before_days=0,
                    minimum_stock_quantity=0,
                    shopping_target_quantity=0,
                    image_url=None,
                    notes="",
                    expected_updated_at=detail["updated_at"],
                )
            with self.assertRaisesRegex(ValueError, "noch von 1 Produkten"):
                local.archive_catalog_master_data("locations", location["id"])

            renamed = local.update_catalog_master_data(
                "locations",
                location["id"],
                name="Vorratsnische",
                description="Umbenannt",
                is_freezer=False,
                name_plural=None,
                expected_updated_at=location["updated_at"],
            )
            self.assertEqual(renamed["name"], "Vorratsnische")
            moved = local.update_catalog_product(
                product["id"],
                name=updated["name"],
                product_group_id=updated["product_group_id"],
                default_location_id=master["locations"][0]["id"],
                default_quantity_unit_id=updated["default_quantity_unit_id"],
                default_best_before_days=updated["default_best_before_days"],
                minimum_stock_quantity=updated["minimum_stock_quantity"],
                shopping_target_quantity=updated["shopping_target_quantity"],
                image_url=updated["image_url"],
                notes=updated["notes"],
                expected_updated_at=updated["updated_at"],
            )
            self.assertEqual(moved["default_location_id"], master["locations"][0]["id"])
            self.assertEqual(
                local.archive_catalog_master_data("locations", location["id"])["active"],
                0,
            )

    async def test_catalog_variant_and_barcode_conflicts_are_transactional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "catalog-variants.db")
            local.initialize()
            first = local.create_catalog_product(name="Variantentest Eins")
            second = local.create_catalog_product(name="Variantentest Zwei")
            first_detail = local.create_catalog_variant(
                first["id"],
                name="500 g",
                brand="Testmarke",
                package_amount=500,
                package_unit="g",
                image_url=None,
            )
            second_detail = local.create_catalog_variant(
                second["id"],
                name="Andere Packung",
                brand="Testmarke",
                package_amount=1,
                package_unit="kg",
                image_url=None,
            )
            first_variant = first_detail["variants"][0]["id"]
            second_variant = second_detail["variants"][0]["id"]
            linked = local.add_catalog_barcode(
                first_variant, barcode="4311596654574", symbology="EAN-13"
            )
            self.assertEqual(linked["barcode_count"], 1)
            with self.assertRaisesRegex(ValueError, "anderen Variante"):
                local.add_catalog_barcode(
                    second_variant, barcode="4311596654574", symbology="EAN-13"
                )
            unlinked = local.delete_catalog_barcode(first_variant, "4311596654574")
            self.assertEqual(unlinked["barcode_count"], 0)
            deleted = local.delete_catalog_variant(first_variant)
            self.assertEqual(deleted["variant_count"], 0)

    async def test_real_product_candidates_are_ranked_by_store_and_cached(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "candidates.db")
            local.initialize()
            candidate = {
                "barcode": "4311596654574",
                "name": "HaferDrink Barista",
                "brand": "REWE Bio",
                "quantity": "1 l",
                "image_url": "https://images.example.test/haferdrink.jpg",
                "stores": ["REWE"],
                "countries": ["en:germany"],
                "source": "Open Facts",
                "source_url": "https://world.openfoodfacts.org/product/4311596654574",
                "database_license": "ODbL-1.0",
                "image_license": "CC-BY-SA",
                "attribution": "Open Food Facts contributors",
            }
            with patch(
                "app.services.product_candidates.search_open_facts",
                new=AsyncMock(return_value=[candidate]),
            ) as external_search:
                first = await find_product_candidates(
                    database=local,
                    provider_settings={"type": "openai", "model": ""},
                    receipt={"store_name": "REWE Markt", "currency": "EUR"},
                    item={
                        "raw_name": "HAFERDRINK BARISTA 1L",
                        "normalized_name": "Haferdrink Barista 1L",
                        "quantity": 1,
                        "unit_price": 2.49,
                    },
                )
                local_product = local.create_catalog_product(name="HaferDrink Barista")
                second = await find_product_candidates(
                    database=local,
                    provider_settings={"type": "openai", "model": ""},
                    receipt={"store_name": "REWE Markt", "currency": "EUR"},
                    item={
                        "raw_name": "HAFERDRINK BARISTA 1L",
                        "normalized_name": "Haferdrink Barista 1L",
                        "quantity": 1,
                        "unit_price": 2.49,
                    },
                )
            external_search.assert_awaited_once()
            self.assertFalse(first["cached"])
            self.assertTrue(second["cached"])
            self.assertEqual(
                second["candidates"][0]["local_product_id"], local_product["id"]
            )
            self.assertTrue(first["candidates"][0]["store_match"])
            self.assertEqual(
                first["candidates"][0]["image_url"],
                "https://images.example.test/haferdrink.jpg",
            )
            self.assertIsNotNone(
                local.get_external_product("open_facts", "4311596654574")
            )

    async def test_candidate_selection_keeps_real_images_after_ai_ranking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "candidate-images.db")
            local.initialize()
            candidates = [
                {
                    "barcode": f"candidate-{index}",
                    "name": "Red Bull Sugarfree",
                    "brand": "Red Bull",
                    "quantity": quantity,
                    "image_url": image_url,
                    "stores": [],
                    "countries": ["deutschland"],
                    "source": "Open Facts",
                    "source_url": f"https://example.test/{index}",
                    "database_license": "ODbL-1.0",
                    "image_license": "CC-BY-SA",
                    "attribution": "Open Food Facts contributors",
                }
                for index, quantity, image_url in (
                    (1, "8pcs", None),
                    (2, "355 ml", None),
                    (3, "250 ml", "https://images.example.test/250.jpg"),
                    (4, "250 ml", "https://images.example.test/250-alt.jpg"),
                )
            ]
            ai_order = {
                "candidate-1": {"confidence": 0.99, "reason": "exakt"},
                "candidate-2": {"confidence": 0.95, "reason": "sehr nah"},
                "candidate-3": {"confidence": 0.30, "reason": "mit Bild"},
                "candidate-4": {"confidence": 0.20, "reason": "mit Bild"},
            }
            with (
                patch(
                    "app.services.product_candidates.search_open_facts",
                    new=AsyncMock(return_value=candidates),
                ),
                patch(
                    "app.services.product_candidates.rank_product_candidates",
                    new=AsyncMock(return_value=ai_order),
                ),
            ):
                result = await find_product_candidates(
                    database=local,
                    provider_settings={"type": "openai", "model": "vision"},
                    receipt={"store_name": "REWE", "currency": "EUR"},
                    item={
                        "raw_name": "R.BULL SUGARFREE",
                        "normalized_name": "Red Bull Sugarfree",
                        "quantity": 2,
                        "unit_price": 0.99,
                    },
                    limit=3,
                )
            self.assertEqual(len(result["candidates"]), 3)
            self.assertEqual(
                sum(bool(candidate["image_url"]) for candidate in result["candidates"]),
                2,
            )
            self.assertIn(
                "candidate-1",
                {candidate["external_id"] for candidate in result["candidates"]},
            )

    def test_receipt_prompt_keeps_continuation_lines_with_previous_product(self) -> None:
        self.assertIn("gehört ausschließlich zu der direkt", SYSTEM_PROMPT)
        self.assertIn("davor gedruckten Produktzeile", SYSTEM_PROMPT)
        self.assertIn("statt eine", SYSTEM_PROMPT)
        self.assertIn("Mengenzeile einer falschen Produktzeile", SYSTEM_PROMPT)

    async def test_confirmed_external_candidate_enriches_local_product_variant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "candidate-confirm.db")
            local.initialize()
            master = local.catalog_master_data()
            product = local.create_catalog_product(
                name="Haferdrink Barista",
                location_id=master["locations"][0]["id"],
                quantity_unit_id=master["quantity_units"][0]["id"],
            )
            candidate = {
                "barcode": "4311596654574",
                "name": "HaferDrink Barista",
                "brand": "REWE Bio",
                "quantity": "1 l",
                "image_url": "https://images.example.test/haferdrink.jpg",
                "source_url": "https://world.openfoodfacts.org/product/4311596654574",
                "database_license": "ODbL-1.0",
                "attribution": "Open Food Facts contributors",
            }
            variant_id = local.attach_external_candidate(
                product_id=product["id"],
                source="open_facts",
                external_id="4311596654574",
                candidate=candidate,
                variant_name=candidate["name"],
                package_amount=1,
                package_unit="l",
            )
            local.create_receipt(
                {"id": "receipt-1", "store_name": "REWE"},
                [{"id": "item-1", "raw_name": "HAFERDRINK BARISTA"}],
            )
            local.update_catalog_item_mapping(
                "receipt-1", "item-1", product["id"], True, variant_id
            )
            item = local.get_receipt("receipt-1")["items"][0]
            self.assertEqual(item["catalog_variant_id"], variant_id)
            self.assertEqual(item["catalog_variant_brand"], "REWE Bio")
            self.assertEqual(
                item["catalog_product_image_url"],
                "https://images.example.test/haferdrink.jpg",
            )
            self.assertEqual(
                local.catalog_product_by_barcode("4311596654574")["id"], product["id"]
            )

    async def test_store_mapping_has_explainable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "evidence.db")
            local.initialize()
            product = local.create_catalog_product(name="Haferdrink")
            local.create_receipt(
                {"id": "receipt-1", "store_name": "REWE"},
                [
                    {
                        "id": "item-1",
                        "raw_name": "HAFER BARISTA",
                        "normalized_name": "Haferdrink Barista",
                    }
                ],
            )
            local.update_catalog_item_mapping(
                "receipt-1", "item-1", product["id"], True
            )
            matched = await match_items(
                database=local,
                grocy=None,
                store_name="REWE Markt",
                items=[
                    {
                        "raw_name": "HAFER BARISTA",
                        "normalized_name": "Haferdrink Barista",
                    }
                ],
            )
            self.assertEqual(matched[0]["match_reason"], "learned_store")
            self.assertEqual(matched[0]["match_evidence"][0]["label"], "Bei REWE gelernt")

    async def test_fuzzy_match_is_only_a_review_suggestion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            local = Database(Path(directory) / "matching.db")
            local.initialize()
            grocy = GrocyClient("http://grocy.test", "secret")
            grocy.products = AsyncMock(  # type: ignore[method-assign]
                return_value=[{"id": 11, "name": "Salami"}]
            )
            matched = await match_items(
                database=local,
                grocy=grocy,
                store_name="REWE",
                items=[{"raw_name": "SALAMISTICKS", "normalized_name": "Salamisticks"}],
            )
            self.assertIsNone(matched[0]["grocy_product_id"])
            self.assertEqual(matched[0]["match_status"], "suggested")
            self.assertEqual(matched[0]["suggested_product_id"], 11)

    async def test_create_product_uses_same_stock_and_purchase_unit(self) -> None:
        client = GrocyClient("http://grocy.test", "secret")
        client._request = AsyncMock(return_value={"created_object_id": 42})  # type: ignore[method-assign]

        product_id = await client.create_product(
            name="Bananen",
            location_id=1,
            quantity_unit_id=7,
            product_group_id=3,
            default_best_before_days=7,
        )

        self.assertEqual(product_id, 42)
        client._request.assert_awaited_once_with(  # type: ignore[attr-defined]
            "POST",
            "objects/products",
            json={
                "name": "Bananen",
                "location_id": 1,
                "qu_id_purchase": 7,
                "qu_id_stock": 7,
                "min_stock_amount": 0,
                "default_best_before_days": 7,
                "product_group_id": 3,
            },
        )

    async def test_ensure_store_reuses_existing_store(self) -> None:
        client = GrocyClient("http://grocy.test", "secret")
        client.stores = AsyncMock(  # type: ignore[method-assign]
            return_value=[{"id": 9, "name": "REWE Liederbach"}]
        )
        client._request = AsyncMock()  # type: ignore[method-assign]

        store_id = await client.ensure_store("  rewe liederbach ")

        self.assertEqual(store_id, 9)
        client._request.assert_not_awaited()  # type: ignore[attr-defined]

    async def test_ensure_location_creates_confirmed_freezer_location(self) -> None:
        client = GrocyClient("http://grocy.test", "secret")
        client._request = AsyncMock(  # type: ignore[method-assign]
            side_effect=[[], {"created_object_id": 4}]
        )

        location_id = await client.ensure_location("Tiefkühler", is_freezer=True)

        self.assertEqual(location_id, 4)
        self.assertEqual(
            client._request.await_args_list[1].kwargs["json"],  # type: ignore[attr-defined]
            {
                "name": "Tiefkühler",
                "active": 1,
                "description": "",
                "is_freezer": 1,
            },
        )

    async def test_ensure_quantity_unit_creates_renamed_suggestion(self) -> None:
        client = GrocyClient("http://grocy.test", "secret")
        client._request = AsyncMock(  # type: ignore[method-assign]
            side_effect=[[], {"created_object_id": 8}]
        )

        unit_id = await client.ensure_quantity_unit("Rolle")

        self.assertEqual(unit_id, 8)
        self.assertEqual(
            client._request.await_args_list[1].kwargs["json"],  # type: ignore[attr-defined]
            {
                "name": "Rolle",
                "active": 1,
                "name_plural": "Rolle",
                "description": "",
            },
        )

    async def test_ensure_product_group_reuses_existing_case_insensitively(self) -> None:
        client = GrocyClient("http://grocy.test", "secret")
        client._request = AsyncMock(  # type: ignore[method-assign]
            return_value=[{"id": 5, "name": "Haushalt & Pflege"}]
        )

        group_id = await client.ensure_product_group(" haushalt & pflege ")

        self.assertEqual(group_id, 5)
        client._request.assert_awaited_once_with(  # type: ignore[attr-defined]
            "GET", "objects/product_groups"
        )

    async def test_purchase_only_sends_explicit_best_before_date(self) -> None:
        client = GrocyClient("http://grocy.test", "secret")
        client._request = AsyncMock(return_value={})  # type: ignore[method-assign]
        await client.add_purchase(
            product_id=4,
            amount=2,
            unit_price=1.25,
            purchased_date="2026-08-10",
            best_before_date="2026-08-31",
            store_id=3,
        )
        client._request.assert_awaited_once_with(  # type: ignore[attr-defined]
            "POST",
            "stock/products/4/add",
            json={
                "amount": 2,
                "transaction_type": "purchase",
                "price": 1.25,
                "purchased_date": "2026-08-10",
                "best_before_date": "2026-08-31",
                "shopping_location_id": 3,
            },
        )

    async def test_grocy_stock_reads_preview_source_without_mutation(self) -> None:
        client = GrocyClient("http://grocy.test", "secret")
        client._request = AsyncMock(  # type: ignore[method-assign]
            return_value=[{"product_id": 4, "amount": "2"}]
        )

        result = await client.stock()

        self.assertEqual(result[0]["product_id"], 4)
        client._request.assert_awaited_once_with("GET", "stock")  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
