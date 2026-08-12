from __future__ import annotations

import base64
import hashlib
import json
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pywebpush import WebPushException, webpush

from ..database import Database, now_iso
from ..security import SecretStore
from .outbound_urls import validate_public_push_destination


VAPID_SETTINGS_KEY = "notifications.webpush.v1"
LAST_CHECKED_KEY = "notifications.last_checked_at"


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _quantity(value: float, locale: str) -> str:
    rounded = round(float(value), 3)
    if rounded.is_integer():
        return str(int(rounded))
    rendered = str(rounded)
    return rendered.replace(".", ",") if locale == "de" else rendered


def _date_label(value: str, locale: str) -> str:
    parsed = datetime.strptime(value, "%Y-%m-%d")
    return parsed.strftime("%d.%m.%Y" if locale == "de" else "%m/%d/%Y")


class NotificationService:
    """Own encrypted browser subscriptions and state-based notification delivery."""

    def __init__(
        self,
        database: Database,
        secret_store: SecretStore,
        *,
        vapid_subject: str,
        sender: Callable[..., Any] = webpush,
    ) -> None:
        self.database = database
        self.secret_store = secret_store
        self.vapid_subject = vapid_subject
        self.sender = sender
        self._lock = threading.RLock()

    def _vapid_keys(self) -> dict[str, str]:
        with self._lock:
            encrypted = self.database.get_setting(VAPID_SETTINGS_KEY)
            if encrypted:
                keys = self.secret_store.decrypt_json(encrypted)
                if keys.get("private_key") and keys.get("public_key"):
                    return {"private_key": str(keys["private_key"]), "public_key": str(keys["public_key"])}

            private_key = ec.generate_private_key(ec.SECP256R1())
            private_der = private_key.private_bytes(
                serialization.Encoding.DER,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
            public_point = private_key.public_key().public_bytes(
                serialization.Encoding.X962,
                serialization.PublicFormat.UncompressedPoint,
            )
            keys = {
                "private_key": _base64url(private_der),
                "public_key": _base64url(public_point),
            }
            self.database.put_setting(
                VAPID_SETTINGS_KEY, self.secret_store.encrypt_json(keys)
            )
            return keys

    @staticmethod
    def _public_subscription(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "endpoint_fingerprint": str(row["endpoint_hash"])[:16],
            "device_name": str(row["device_name"]),
            "active": bool(row["active"]),
            "failure_count": int(row["failure_count"]),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "last_success_at": row.get("last_success_at"),
            "last_failure_at": row.get("last_failure_at"),
        }

    def _ensure_preferences(self, user_id: str, household_id: str) -> dict[str, Any]:
        timestamp = now_iso()
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO notification_preferences(
                    user_id, household_id, push_enabled, low_stock_enabled,
                    expiry_enabled, expiry_days_before, created_at, updated_at
                ) VALUES (?, ?, 0, 1, 1, 7, ?, ?)
                ON CONFLICT(user_id) DO NOTHING
                """,
                (user_id, household_id, timestamp, timestamp),
            )
            row = conn.execute(
                "SELECT * FROM notification_preferences WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            raise RuntimeError("Benachrichtigungseinstellungen konnten nicht geladen werden")
        return dict(row)

    def state(self, user_id: str, household_id: str) -> dict[str, Any]:
        preferences = self._ensure_preferences(user_id, household_id)
        with self.database.connect() as conn:
            subscriptions = conn.execute(
                """
                SELECT * FROM push_subscriptions
                WHERE user_id = ? AND revoked_at IS NULL
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
            counts = {
                str(row["kind"]): int(row["count"])
                for row in conn.execute(
                    """
                    SELECT kind, COUNT(*) AS count FROM notification_events
                    WHERE user_id = ? AND active = 1 GROUP BY kind
                    """,
                    (user_id,),
                ).fetchall()
            }
        return {
            "public_key": self._vapid_keys()["public_key"],
            "secure_context_required": True,
            "preferences": {
                "push_enabled": bool(preferences["push_enabled"]),
                "low_stock_enabled": bool(preferences["low_stock_enabled"]),
                "expiry_enabled": bool(preferences["expiry_enabled"]),
                "expiry_days_before": int(preferences["expiry_days_before"]),
            },
            "subscriptions": [
                self._public_subscription(dict(row)) for row in subscriptions
            ],
            "active_low_stock_events": counts.get("low_stock", 0),
            "active_expiry_events": counts.get("expiry", 0),
            "last_checked_at": self.database.get_setting(LAST_CHECKED_KEY),
        }

    def save_preferences(
        self,
        user_id: str,
        household_id: str,
        *,
        push_enabled: bool,
        low_stock_enabled: bool,
        expiry_enabled: bool,
        expiry_days_before: int,
    ) -> dict[str, Any]:
        self._ensure_preferences(user_id, household_id)
        with self.database.connect() as conn:
            conn.execute(
                """
                UPDATE notification_preferences SET
                    household_id = ?, push_enabled = ?, low_stock_enabled = ?,
                    expiry_enabled = ?, expiry_days_before = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (
                    household_id,
                    int(push_enabled),
                    int(low_stock_enabled),
                    int(expiry_enabled),
                    expiry_days_before,
                    now_iso(),
                    user_id,
                ),
            )
            disabled_kinds = []
            if not push_enabled or not low_stock_enabled:
                disabled_kinds.append("low_stock")
            if not push_enabled or not expiry_enabled:
                disabled_kinds.append("expiry")
            if disabled_kinds:
                timestamp = now_iso()
                for kind in disabled_kinds:
                    conn.execute(
                        """
                        UPDATE notification_events
                        SET active = 0, resolved_at = ?, updated_at = ?
                        WHERE user_id = ? AND active = 1 AND kind = ?
                        """,
                        (timestamp, timestamp, user_id, kind),
                    )
        return self.state(user_id, household_id)

    def save_subscription(
        self,
        user_id: str,
        household_id: str,
        *,
        subscription: dict[str, Any],
        device_name: str,
    ) -> dict[str, Any]:
        endpoint = validate_public_push_destination(str(subscription["endpoint"]))
        endpoint_hash = hashlib.sha256(endpoint.encode("utf-8")).hexdigest()
        encrypted = self.secret_store.encrypt_json(subscription)
        timestamp = now_iso()
        with self.database.connect() as conn:
            existing = conn.execute(
                "SELECT id, user_id FROM push_subscriptions WHERE endpoint_hash = ?",
                (endpoint_hash,),
            ).fetchone()
            if existing and str(existing["user_id"]) != user_id:
                raise ValueError("Dieses Gerät gehört bereits zu einem anderen Konto")
            subscription_id = str(existing["id"]) if existing else str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO push_subscriptions(
                    id, endpoint_hash, household_id, user_id, subscription_encrypted,
                    device_name, active, failure_count, created_at, updated_at,
                    last_success_at, last_failure_at, revoked_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, ?, NULL, NULL, NULL)
                ON CONFLICT(endpoint_hash) DO UPDATE SET
                    household_id = excluded.household_id,
                    subscription_encrypted = excluded.subscription_encrypted,
                    device_name = excluded.device_name,
                    active = 1,
                    failure_count = 0,
                    updated_at = excluded.updated_at,
                    last_failure_at = NULL,
                    revoked_at = NULL
                """,
                (
                    subscription_id,
                    endpoint_hash,
                    household_id,
                    user_id,
                    encrypted,
                    device_name.strip()[:100] or "Vorrio-Gerät",
                    timestamp,
                    timestamp,
                ),
            )
            row = conn.execute(
                "SELECT * FROM push_subscriptions WHERE id = ?", (subscription_id,)
            ).fetchone()
        if not row:
            raise RuntimeError("Push-Gerät konnte nicht gespeichert werden")
        return self._public_subscription(dict(row))

    def revoke_subscription(self, user_id: str, subscription_id: str) -> bool:
        timestamp = now_iso()
        with self.database.connect() as conn:
            updated = conn.execute(
                """
                UPDATE push_subscriptions SET active = 0, revoked_at = ?, updated_at = ?
                WHERE id = ? AND user_id = ? AND revoked_at IS NULL
                """,
                (timestamp, timestamp, subscription_id, user_id),
            ).rowcount
        return bool(updated)

    def _subscriptions(self, user_id: str) -> list[dict[str, Any]]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM push_subscriptions
                WHERE user_id = ? AND active = 1 AND revoked_at IS NULL
                ORDER BY created_at
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _record_delivery(
        self,
        *,
        event_id: str | None,
        subscription: dict[str, Any],
        kind: str,
        success: bool,
        status_code: int | None,
        error: str | None,
    ) -> None:
        timestamp = now_iso()
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO notification_deliveries(
                    id, event_id, subscription_id, household_id, user_id,
                    kind, outcome, status_code, error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    event_id,
                    subscription["id"],
                    subscription["household_id"],
                    subscription["user_id"],
                    kind,
                    "success" if success else "failure",
                    status_code,
                    (error or "")[:500] or None,
                    timestamp,
                ),
            )
            if success:
                conn.execute(
                    """
                    UPDATE push_subscriptions SET failure_count = 0,
                        last_success_at = ?, updated_at = ? WHERE id = ?
                    """,
                    (timestamp, timestamp, subscription["id"]),
                )
            else:
                terminal = status_code in {404, 410}
                conn.execute(
                    """
                    UPDATE push_subscriptions SET
                        failure_count = failure_count + 1,
                        last_failure_at = ?, updated_at = ?,
                        active = CASE WHEN ? THEN 0 ELSE active END,
                        revoked_at = CASE WHEN ? THEN ? ELSE revoked_at END
                    WHERE id = ?
                    """,
                    (
                        timestamp,
                        timestamp,
                        int(terminal),
                        int(terminal),
                        timestamp,
                        subscription["id"],
                    ),
                )

    def _send(
        self,
        subscription: dict[str, Any],
        payload: dict[str, Any],
        *,
        event_id: str | None,
        kind: str,
    ) -> bool:
        status_code: int | None = None
        try:
            info = self.secret_store.decrypt_json(
                str(subscription["subscription_encrypted"])
            )
            validate_public_push_destination(str(info.get("endpoint") or ""))
            response = self.sender(
                subscription_info=info,
                data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                vapid_private_key=self._vapid_keys()["private_key"],
                vapid_claims={"sub": self.vapid_subject},
                ttl=60 * 60,
                timeout=10,
            )
            status_code = int(getattr(response, "status_code", 201))
            self._record_delivery(
                event_id=event_id,
                subscription=subscription,
                kind=kind,
                success=True,
                status_code=status_code,
                error=None,
            )
            return True
        except WebPushException as exc:
            response = getattr(exc, "response", None)
            status_code = int(response.status_code) if response is not None else None
            error = str(exc)
        except Exception as exc:  # pragma: no cover - defensive boundary around push providers
            error = str(exc)
        self._record_delivery(
            event_id=event_id,
            subscription=subscription,
            kind=kind,
            success=False,
            status_code=status_code,
            error=error,
        )
        return False

    def send_test(self, user_id: str, subscription_id: str) -> dict[str, Any]:
        subscriptions = [
            row for row in self._subscriptions(user_id) if row["id"] == subscription_id
        ]
        if not subscriptions:
            raise KeyError("Push-Gerät nicht gefunden")
        locale = self.database.get_user_locale(user_id)
        delivered = self._send(
            subscriptions[0],
            {
                "title": "Vorrio ist bereit" if locale == "de" else "Vorrio is ready",
                "body": (
                    "Test erfolgreich – dieses Gerät erhält Vorratsmeldungen."
                    if locale == "de"
                    else "Test successful – this device will receive stock notifications."
                ),
                "url": "/",
                "tag": "vorrio-test",
                "kind": "test",
                "locale": locale,
            },
            event_id=None,
            kind="test",
        )
        return {"delivered": int(delivered), "failed": int(not delivered)}

    def _conditions(self, expiry_days_before: int, locale: str) -> list[dict[str, Any]]:
        deadline = (datetime.now(UTC).date() + timedelta(days=expiry_days_before)).isoformat()
        with self.database.connect() as conn:
            low_stock = conn.execute(
                """
                SELECT p.id AS subject_id, p.name,
                    COALESCE(SUM(l.quantity), 0) AS current_quantity,
                    p.minimum_stock_quantity AS minimum_quantity,
                    u.name AS unit_name
                FROM catalog_products p
                LEFT JOIN stock_lots l ON l.product_id = p.id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                WHERE p.active = 1 AND p.minimum_stock_quantity > 0
                GROUP BY p.id
                HAVING COALESCE(SUM(l.quantity), 0) <= p.minimum_stock_quantity
                ORDER BY p.name COLLATE NOCASE
                """
            ).fetchall()
            expiry = conn.execute(
                """
                SELECT l.id AS subject_id, p.name, l.quantity,
                    l.best_before_date, u.name AS unit_name
                FROM stock_lots l
                JOIN catalog_products p ON p.id = l.product_id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                WHERE p.active = 1 AND l.quantity > 0
                    AND l.best_before_date IS NOT NULL
                    AND l.best_before_date <= ?
                ORDER BY l.best_before_date, p.name COLLATE NOCASE
                """,
                (deadline,),
            ).fetchall()
        conditions: list[dict[str, Any]] = []
        for source in low_stock:
            row = dict(source)
            unit = f" {row['unit_name']}" if row.get("unit_name") else ""
            conditions.append(
                {
                    "kind": "low_stock",
                    "subject_id": str(row["subject_id"]),
                    "condition_key": f"{row['current_quantity']}:{row['minimum_quantity']}",
                    "title": "Vorrat wird knapp" if locale == "de" else "Stock is running low",
                    "body": (
                        f"{row['name']}: {_quantity(row['current_quantity'], locale)}{unit} "
                        f"vorhanden, Mindestbestand {_quantity(row['minimum_quantity'], locale)}."
                        if locale == "de"
                        else f"{row['name']}: {_quantity(row['current_quantity'], locale)}{unit} "
                        f"available, minimum stock {_quantity(row['minimum_quantity'], locale)}."
                    ),
                    "url": "/",
                    "tag": f"vorrio-low-stock-{row['subject_id']}",
                }
            )
        today = datetime.now(UTC).date().isoformat()
        for source in expiry:
            row = dict(source)
            expired = str(row["best_before_date"]) < today
            when = (
                "ist abgelaufen"
                if locale == "de" and expired
                else f"läuft am {_date_label(str(row['best_before_date']), locale)} ab"
                if locale == "de"
                else "has expired"
                if expired
                else f"expires on {_date_label(str(row['best_before_date']), locale)}"
            )
            conditions.append(
                {
                    "kind": "expiry",
                    "subject_id": str(row["subject_id"]),
                    "condition_key": str(row["best_before_date"]),
                    "title": "Haltbarkeit prüfen" if locale == "de" else "Check shelf life",
                    "body": f"{row['name']} {when}.",
                    "url": "/",
                    "tag": f"vorrio-expiry-{row['subject_id']}",
                }
            )
        return conditions

    def _activate_event(
        self, user_id: str, household_id: str, condition: dict[str, Any]
    ) -> tuple[str, bool]:
        timestamp = now_iso()
        with self.database.connect() as conn:
            existing = conn.execute(
                """
                SELECT * FROM notification_events
                WHERE user_id = ? AND kind = ? AND subject_id = ?
                """,
                (user_id, condition["kind"], condition["subject_id"]),
            ).fetchone()
            should_send = not existing or not bool(existing["active"]) or not existing["last_notified_at"]
            event_id = str(existing["id"]) if existing else str(uuid.uuid4())
            if existing:
                conn.execute(
                    """
                    UPDATE notification_events SET household_id = ?, condition_key = ?,
                        active = 1, resolved_at = NULL, updated_at = ? WHERE id = ?
                    """,
                    (household_id, condition["condition_key"], timestamp, event_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO notification_events(
                        id, household_id, user_id, kind, subject_id, condition_key,
                        active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        event_id,
                        household_id,
                        user_id,
                        condition["kind"],
                        condition["subject_id"],
                        condition["condition_key"],
                        timestamp,
                        timestamp,
                    ),
                )
        return event_id, should_send

    def evaluate_and_send(self) -> dict[str, int]:
        result = {"evaluated_users": 0, "events": 0, "delivered": 0, "failed": 0}
        with self._lock:
            with self.database.connect() as conn:
                users = conn.execute(
                    """
                    SELECT p.* FROM notification_preferences p
                    WHERE p.push_enabled = 1
                      AND EXISTS (
                        SELECT 1 FROM push_subscriptions s
                        WHERE s.user_id = p.user_id AND s.active = 1 AND s.revoked_at IS NULL
                      )
                    """
                ).fetchall()
            for source in users:
                preferences = dict(source)
                user_id = str(preferences["user_id"])
                household_id = str(preferences["household_id"])
                locale = self.database.get_user_locale(user_id)
                enabled_kinds = {
                    kind
                    for kind, enabled in (
                        ("low_stock", preferences["low_stock_enabled"]),
                        ("expiry", preferences["expiry_enabled"]),
                    )
                    if bool(enabled)
                }
                conditions = [
                    condition
                    for condition in self._conditions(int(preferences["expiry_days_before"]), locale)
                    if condition["kind"] in enabled_kinds
                ]
                active_keys = {(item["kind"], item["subject_id"]) for item in conditions}
                with self.database.connect() as conn:
                    existing = conn.execute(
                        "SELECT id, kind, subject_id FROM notification_events WHERE user_id = ? AND active = 1",
                        (user_id,),
                    ).fetchall()
                    timestamp = now_iso()
                    for event in existing:
                        if (str(event["kind"]), str(event["subject_id"])) not in active_keys:
                            conn.execute(
                                "UPDATE notification_events SET active = 0, resolved_at = ?, updated_at = ? WHERE id = ?",
                                (timestamp, timestamp, event["id"]),
                            )
                subscriptions = self._subscriptions(user_id)
                for condition in conditions:
                    event_id, should_send = self._activate_event(user_id, household_id, condition)
                    if not should_send:
                        continue
                    result["events"] += 1
                    payload = {
                        key: condition[key]
                        for key in ("title", "body", "url", "tag", "kind")
                    }
                    payload["locale"] = locale
                    delivered = 0
                    for subscription in subscriptions:
                        if self._send(
                            subscription,
                            payload,
                            event_id=event_id,
                            kind=str(condition["kind"]),
                        ):
                            result["delivered"] += 1
                            delivered += 1
                        else:
                            result["failed"] += 1
                    if delivered:
                        with self.database.connect() as conn:
                            conn.execute(
                                "UPDATE notification_events SET last_notified_at = ?, updated_at = ? WHERE id = ?",
                                (now_iso(), now_iso(), event_id),
                            )
                result["evaluated_users"] += 1
            self.database.put_setting(LAST_CHECKED_KEY, now_iso())
            with self.database.connect() as conn:
                cutoff = (datetime.now(UTC) - timedelta(days=90)).isoformat(timespec="microseconds")
                conn.execute(
                    "DELETE FROM notification_deliveries WHERE created_at < ?", (cutoff,)
                )
        return result
