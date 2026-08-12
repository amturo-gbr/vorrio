from __future__ import annotations

import secrets
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from .database import Database, now_iso
from .security import SecretStore


SETTINGS_KEYS = ("connections.v1", "notifications.webpush.v1")


def rotate_secret(database_path: Path, old_secret: str, new_secret: str) -> Path:
    if not database_path.is_file():
        raise RuntimeError(f"Datenbank nicht gefunden: {database_path}")
    if len(old_secret) < 1:
        raise RuntimeError("APP_SECRET_KEY fehlt")
    if len(new_secret) < 32:
        raise RuntimeError("APP_SECRET_KEY_NEW muss mindestens 32 Zeichen lang sein")
    if secrets.compare_digest(old_secret, new_secret):
        raise RuntimeError("Der neue Schlüssel muss sich vom bisherigen unterscheiden")

    old_store = SecretStore(old_secret)
    new_store = SecretStore(new_secret)
    with closing(sqlite3.connect(database_path)) as source:
        tables = {
            str(row[0])
            for row in source.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        encrypted_settings: dict[str, dict] = {}
        for key in SETTINGS_KEYS:
            row = source.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
            if row:
                encrypted_settings[key] = old_store.decrypt_json(str(row[0]))
        subscriptions = [
            (str(row[0]), old_store.decrypt_json(str(row[1])))
            for row in source.execute(
                "SELECT id, subscription_encrypted FROM push_subscriptions"
            ).fetchall()
        ] if "push_subscriptions" in tables else []
        totp_credentials = [
            (str(row[0]), old_store.decrypt_json(str(row[1])))
            for row in source.execute(
                "SELECT user_id, secret_encrypted FROM totp_credentials"
            ).fetchall()
        ] if "totp_credentials" in tables else []

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = database_path.with_name(
            f"{database_path.name}.backup_before_secret_rotation_{timestamp}"
        )
        with closing(sqlite3.connect(backup_path)) as backup:
            source.backup(backup)

    database = Database(database_path)
    database.initialize()
    for key, value in encrypted_settings.items():
        database.put_setting(key, new_store.encrypt_json(value))
    with database.connect() as conn:
        for subscription_id, value in subscriptions:
            conn.execute(
                "UPDATE push_subscriptions SET subscription_encrypted = ?, updated_at = ? WHERE id = ?",
                (new_store.encrypt_json(value), now_iso(), subscription_id),
            )
        for user_id, value in totp_credentials:
            conn.execute(
                "UPDATE totp_credentials SET secret_encrypted = ?, updated_at = ? WHERE user_id = ?",
                (new_store.encrypt_json(value), now_iso(), user_id),
            )
        conn.execute(
            "UPDATE auth_sessions SET revoked_at = ? WHERE revoked_at IS NULL",
            (now_iso(),),
        )
    database.add_audit_event(
        category="security",
        action="app_secret_rotation",
        outcome="success",
        details={"sessions_invalidated": True},
    )
    return backup_path
