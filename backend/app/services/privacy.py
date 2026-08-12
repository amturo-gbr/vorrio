from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import tempfile
import uuid
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..database import Database, now_iso
from .product_images import is_managed_product_image_url


EXPORT_EXCLUSIONS = (
    "password hashes",
    "session and invitation tokens",
    "API-token hashes",
    "TOTP secrets and recovery-code hashes",
    "passkey public-key material and challenges",
    "provider and connector API keys",
    "push endpoints and browser encryption keys",
    "network source fingerprints",
)

AUDIT_ROUTE_PATTERNS = (
    re.compile(r"(/api/v1/auth/(?:sessions|passkeys|api-tokens|members|invitations)/)[^/\s]+"),
    re.compile(r"(/api/v1/catalog/products/)[^/\s]+"),
    re.compile(r"(/api/v1/catalog/variants/)[^/\s]+"),
    re.compile(r"(/api/v1/receipts/)(?!analyze(?:/|$))[^/\s]+"),
    re.compile(r"(/api/v1/scans/)(?!(?:resolve|unresolved)(?:/|$))[^/\s]+"),
    re.compile(r"(/api/v1/shopping-list/)(?!(?:low-stock|generate)(?:/|$))[^/\s]+"),
    re.compile(r"(/api/v1/notifications/subscriptions/)[^/\s]+"),
    re.compile(r"(/items/)[^/\s]+"),
    re.compile(r"(/barcodes/)[^/\s]+"),
    re.compile(r"(/master-data/[^/\s]+/)[^/\s]+"),
)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(query, params).fetchall()]


def sanitize_audit_action(action: str) -> str:
    sanitized = action
    for pattern in AUDIT_ROUTE_PATTERNS:
        sanitized = pattern.sub(r"\1{id}", sanitized)
    return sanitized


def _safe_receipt_path(data_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    receipts_root = (data_dir / "receipts").resolve()
    candidate = Path(value).resolve()
    try:
        candidate.relative_to(receipts_root)
    except ValueError:
        return None
    return candidate


def _safe_product_image_path(
    data_dir: Path, product_id: str, image_url: str | None
) -> Path | None:
    if not is_managed_product_image_url(image_url, product_id):
        return None
    try:
        normalized_id = str(uuid.UUID(product_id))
    except ValueError:
        return None
    root = (data_dir / "product-images").resolve()
    candidate = (root / f"{normalized_id}.webp").resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


class PrivacyService:
    def __init__(self, database: Database, data_dir: Path) -> None:
        self.database = database
        self.data_dir = data_dir

    def retention_preview(self, *, delete_after_analysis: bool, retention_days: int) -> dict[str, Any]:
        cutoff = datetime.now(UTC) if delete_after_analysis else datetime.now(UTC) - timedelta(days=retention_days)
        with self.database.connect() as conn:
            records = _rows(
                conn,
                """
                SELECT id, image_path, created_at
                FROM receipts
                WHERE image_path IS NOT NULL AND created_at <= ?
                ORDER BY created_at
                """,
                (cutoff.isoformat(),),
            )
            retained = _rows(
                conn,
                "SELECT id, image_path FROM receipts WHERE image_path IS NOT NULL",
            )
        expired_bytes = 0
        retained_bytes = 0
        for row in retained:
            path = _safe_receipt_path(self.data_dir, row.get("image_path"))
            if path and path.is_file():
                retained_bytes += path.stat().st_size
        for row in records:
            path = _safe_receipt_path(self.data_dir, row.get("image_path"))
            if path and path.is_file():
                expired_bytes += path.stat().st_size
        return {
            "delete_after_analysis": delete_after_analysis,
            "retention_days": retention_days,
            "retained_file_count": len(retained),
            "retained_bytes": retained_bytes,
            "expired_file_count": len(records),
            "expired_bytes": expired_bytes,
            "cutoff": cutoff.isoformat(),
        }

    def prune_receipt_files(self, *, delete_after_analysis: bool, retention_days: int) -> dict[str, Any]:
        preview = self.retention_preview(
            delete_after_analysis=delete_after_analysis,
            retention_days=retention_days,
        )
        cutoff = str(preview["cutoff"])
        with self.database.connect() as conn:
            records = _rows(
                conn,
                """
                SELECT id, image_path FROM receipts
                WHERE image_path IS NOT NULL AND created_at <= ?
                """,
                (cutoff,),
            )
        cleared: list[str] = []
        deleted_files = 0
        deleted_bytes = 0
        rejected_paths = 0
        for row in records:
            path = _safe_receipt_path(self.data_dir, row.get("image_path"))
            if not path:
                rejected_paths += 1
                continue
            if path.is_file():
                deleted_bytes += path.stat().st_size
                path.unlink()
                deleted_files += 1
            cleared.append(str(row["id"]))
        if cleared:
            with self.database.connect() as conn:
                conn.executemany(
                    "UPDATE receipts SET image_path = NULL, updated_at = ? WHERE id = ?",
                    [(now_iso(), receipt_id) for receipt_id in cleared],
                )
        return {
            "deleted_file_count": deleted_files,
            "deleted_bytes": deleted_bytes,
            "cleared_receipt_count": len(cleared),
            "rejected_path_count": rejected_paths,
            "completed_at": now_iso(),
        }

    def export_preview(self, household_id: str) -> dict[str, Any]:
        with self.database.connect() as conn:
            household = conn.execute(
                "SELECT name FROM households WHERE id = ?", (household_id,)
            ).fetchone()
            if not household:
                raise KeyError("Haushalt nicht gefunden")
            counts = {
                "members": int(conn.execute(
                    "SELECT COUNT(*) FROM household_memberships WHERE household_id = ?",
                    (household_id,),
                ).fetchone()[0]),
                "products": int(conn.execute("SELECT COUNT(*) FROM catalog_products").fetchone()[0]),
                "variants": int(conn.execute("SELECT COUNT(*) FROM catalog_product_variants").fetchone()[0]),
                "barcodes": int(conn.execute("SELECT COUNT(*) FROM catalog_barcodes").fetchone()[0]),
                "receipts": int(conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]),
                "receipt_items": int(conn.execute("SELECT COUNT(*) FROM receipt_items").fetchone()[0]),
                "stock_lots": int(conn.execute("SELECT COUNT(*) FROM stock_lots").fetchone()[0]),
                "stock_movements": int(conn.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0]),
                "shopping_items": int(conn.execute("SELECT COUNT(*) FROM shopping_list_items").fetchone()[0]),
            }
            files = _rows(conn, "SELECT image_path FROM receipts WHERE image_path IS NOT NULL")
            product_images = _rows(
                conn,
                "SELECT id, image_url FROM catalog_products WHERE image_url IS NOT NULL",
            )
        file_count = 0
        file_bytes = 0
        for row in files:
            path = _safe_receipt_path(self.data_dir, row.get("image_path"))
            if path and path.is_file():
                file_count += 1
                file_bytes += path.stat().st_size
        product_image_file_count = 0
        product_image_file_bytes = 0
        for row in product_images:
            path = _safe_product_image_path(
                self.data_dir, str(row["id"]), row.get("image_url")
            )
            if path and path.is_file():
                product_image_file_count += 1
                product_image_file_bytes += path.stat().st_size
        return {
            "household_name": str(household["name"]),
            "counts": counts,
            "receipt_file_count": file_count,
            "receipt_file_bytes": file_bytes,
            "product_image_file_count": product_image_file_count,
            "product_image_file_bytes": product_image_file_bytes,
            "excluded_secret_categories": list(EXPORT_EXCLUSIONS),
        }

    def build_export(
        self,
        *,
        household_id: str,
        public_settings: dict[str, Any],
        include_receipt_files: bool,
        version: str,
    ) -> tuple[tempfile.SpooledTemporaryFile[bytes], dict[str, Any]]:
        preview = self.export_preview(household_id)
        with self.database.connect() as conn:
            sections: dict[str, Any] = {
                "household": _rows(
                    conn,
                    "SELECT id, name, created_at, updated_at FROM households WHERE id = ?",
                    (household_id,),
                ),
                "members": _rows(
                    conn,
                    """
                    SELECT u.id, u.display_name, u.email, u.active, u.owner_setup_complete,
                           u.created_at, u.updated_at, m.role, m.active AS membership_active,
                           m.created_at AS membership_created_at
                    FROM household_memberships m
                    JOIN users u ON u.id = m.user_id
                    WHERE m.household_id = ?
                    ORDER BY u.created_at
                    """,
                    (household_id,),
                ),
                "invitations": _rows(
                    conn,
                    """
                    SELECT id, invited_by_user_id, display_name, email, role, expires_at,
                           accepted_at, revoked_at, created_at
                    FROM household_invitations WHERE household_id = ?
                    """,
                    (household_id,),
                ),
                "devices": {
                    "browser_sessions": _rows(
                        conn,
                        """
                        SELECT id, user_id, device_name, created_at, last_seen_at, expires_at,
                               revoked_at, authenticated_at, authentication_method
                        FROM auth_sessions WHERE household_id = ?
                        """,
                        (household_id,),
                    ),
                    "passkeys": _rows(
                        conn,
                        """
                        SELECT w.id, w.user_id, w.device_type, w.backed_up, w.name,
                               w.created_at, w.last_used_at
                        FROM webauthn_credentials w
                        JOIN household_memberships m ON m.user_id = w.user_id
                        WHERE m.household_id = ?
                        """,
                        (household_id,),
                    ),
                    "api_tokens": _rows(
                        conn,
                        """
                        SELECT id, user_id, name, scopes_json, expires_at, created_at,
                               last_used_at, revoked_at
                        FROM api_tokens WHERE household_id = ?
                        """,
                        (household_id,),
                    ),
                    "push_devices": _rows(
                        conn,
                        """
                        SELECT id, user_id, device_name, active, failure_count, created_at,
                               updated_at, last_success_at, last_failure_at, revoked_at
                        FROM push_subscriptions WHERE household_id = ?
                        """,
                        (household_id,),
                    ),
                },
                "preferences": {
                    "application": public_settings,
                    "notifications": _rows(
                        conn,
                        """
                        SELECT user_id, push_enabled, low_stock_enabled, expiry_enabled,
                               expiry_days_before, created_at, updated_at
                        FROM notification_preferences WHERE household_id = ?
                        """,
                        (household_id,),
                    ),
                    "budget": _rows(
                        conn,
                        """
                        SELECT monthly_limit_cents, currency, warning_percent,
                               updated_by_user_id, created_at, updated_at
                        FROM household_budget_settings WHERE household_id = ?
                        """,
                        (household_id,),
                    ),
                },
                "catalog": {
                    # Names are the literal export allow-list immediately below.
                    table: _rows(conn, f"SELECT * FROM {table}")  # nosec B608
                    for table in (
                        "catalog_locations",
                        "catalog_quantity_units",
                        "catalog_product_groups",
                        "catalog_products",
                        "catalog_product_variants",
                        "catalog_barcodes",
                        "catalog_external_refs",
                        "catalog_aliases",
                        "catalog_product_mappings",
                        "product_aliases",
                        "product_mappings",
                    )
                },
                "receipts": {
                    "receipts": _rows(conn, "SELECT * FROM receipts ORDER BY created_at"),
                    "items": _rows(conn, "SELECT * FROM receipt_items ORDER BY receipt_id, position"),
                    "import_runs": _rows(conn, "SELECT * FROM import_runs ORDER BY created_at"),
                },
                "stock": {
                    table: _rows(conn, f"SELECT * FROM {table}")  # nosec B608
                    for table in (
                        "stock_lots",
                        "stock_movements",
                        "stock_count_sessions",
                        "stock_count_lines",
                    )
                },
                "shopping": {
                    table: _rows(conn, f"SELECT * FROM {table}")  # nosec B608
                    for table in (
                        "shopping_list_items",
                        "shopping_generation_runs",
                        "shopping_generation_items",
                    )
                },
                "scans": _rows(conn, "SELECT * FROM scan_drafts ORDER BY created_at"),
                "audit": _rows(
                    conn,
                    "SELECT id, category, action, outcome, created_at FROM audit_events ORDER BY created_at",
                ),
            }

        receipt_source_paths = {
            str(receipt["id"]): receipt.get("image_path")
            for receipt in sections["receipts"]["receipts"]
        }
        product_image_paths = {
            str(product["id"]): _safe_product_image_path(
                self.data_dir, str(product["id"]), product.get("image_url")
            )
            for product in sections["catalog"]["catalog_products"]
        }
        for receipt in sections["receipts"]["receipts"]:
            if receipt.get("image_path"):
                receipt["image_path"] = Path(str(receipt["image_path"])).name
        for event in sections["audit"]:
            event["action"] = sanitize_audit_action(str(event["action"]))

        archive = tempfile.SpooledTemporaryFile(max_size=16 * 1024 * 1024, mode="w+b")
        generated_at = now_iso()
        manifest: dict[str, Any] = {
            "format": "vorrio-portable-export",
            "format_version": 1,
            "vorrio_version": version,
            "generated_at": generated_at,
            "household_name": preview["household_name"],
            "counts": preview["counts"],
            "receipt_files_included": 0,
            "receipt_file_bytes": 0,
            "product_images_included": 0,
            "product_image_bytes": 0,
            "excluded_secret_categories": list(EXPORT_EXCLUSIONS),
            "files": [],
        }
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for name, payload in sections.items():
                body = _json_bytes(payload)
                archive_name = f"data/{name}.json"
                bundle.writestr(archive_name, body)
                manifest["files"].append({
                    "path": archive_name,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                })
            if include_receipt_files:
                for receipt in sections["receipts"]["receipts"]:
                    path = _safe_receipt_path(
                        self.data_dir,
                        receipt_source_paths.get(str(receipt["id"])),
                    )
                    if not path or not path.is_file():
                        continue
                    body = path.read_bytes()
                    archive_name = f"receipt-files/{receipt['id']}{path.suffix.lower()}"
                    bundle.writestr(archive_name, body)
                    manifest["receipt_files_included"] += 1
                    manifest["receipt_file_bytes"] += len(body)
                    manifest["files"].append({
                        "path": archive_name,
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                    })
            for product_id, path in product_image_paths.items():
                if not path or not path.is_file():
                    continue
                body = path.read_bytes()
                archive_name = f"product-images/{product_id}.webp"
                bundle.writestr(archive_name, body)
                manifest["product_images_included"] += 1
                manifest["product_image_bytes"] += len(body)
                manifest["files"].append({
                    "path": archive_name,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                })
            bundle.writestr("manifest.json", _json_bytes(manifest))
        archive.seek(0)
        return archive, manifest

    def operational_overview(
        self,
        *,
        household_id: str,
        delete_after_analysis: bool,
        retention_days: int,
        event_limit: int = 40,
    ) -> dict[str, Any]:
        preview = self.retention_preview(
            delete_after_analysis=delete_after_analysis,
            retention_days=retention_days,
        )
        cutoff = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        with self.database.connect() as conn:
            integrity = str(conn.execute("PRAGMA quick_check").fetchone()[0])
            counts = dict(conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM users u JOIN household_memberships m ON m.user_id=u.id
                     WHERE m.household_id=? AND u.active=1 AND m.active=1) AS active_users,
                    (SELECT COUNT(*) FROM auth_sessions WHERE household_id=? AND revoked_at IS NULL) AS active_sessions,
                    (SELECT COUNT(*) FROM api_tokens WHERE household_id=? AND revoked_at IS NULL AND expires_at>?) AS active_api_tokens,
                    (SELECT COUNT(*) FROM push_subscriptions WHERE household_id=? AND active=1) AS active_push_devices,
                    (SELECT COUNT(*) FROM receipts WHERE status='review') AS pending_receipts,
                    (SELECT COUNT(*) FROM catalog_products WHERE active=1) AS products,
                    (SELECT COUNT(*) FROM stock_lots WHERE quantity>0) AS stock_lots,
                    (SELECT COUNT(*) FROM audit_events WHERE outcome='failure' AND created_at>=?) AS failures_24h
                """,
                (household_id, household_id, household_id, now_iso(), household_id, cutoff),
            ).fetchone())
            users = {
                str(row["id"]): str(row["display_name"])
                for row in conn.execute(
                    """
                    SELECT u.id, u.display_name FROM users u
                    JOIN household_memberships m ON m.user_id=u.id
                    WHERE m.household_id=?
                    """,
                    (household_id,),
                ).fetchall()
            }
            rows = _rows(
                conn,
                """
                SELECT id, category, action, outcome, details_json, created_at
                FROM audit_events ORDER BY created_at DESC, rowid DESC LIMIT ?
                """,
                (max(1, min(event_limit, 100)),),
            )
        events: list[dict[str, Any]] = []
        for row in rows:
            try:
                details = json.loads(str(row.pop("details_json")))
            except (json.JSONDecodeError, TypeError):
                details = {}
            actor_id = details.get("actor_user_id") or details.get("user_id")
            events.append({
                **row,
                "action": sanitize_audit_action(str(row["action"])),
                "actor_label": users.get(str(actor_id), "System") if actor_id else "System",
            })
        return {
            "database_integrity": integrity,
            "database_bytes": self.database.path.stat().st_size if self.database.path.is_file() else 0,
            "counts": {key: int(value or 0) for key, value in counts.items()},
            "retention": preview,
            "recent_events": events,
            "generated_at": now_iso(),
        }

    def erase_installation(self) -> dict[str, Any]:
        receipt_root = (self.data_dir / "receipts").resolve()
        deleted_receipt_files = 0
        deleted_receipt_bytes = 0
        if receipt_root.is_dir():
            for path in receipt_root.iterdir():
                if path.is_file():
                    deleted_receipt_bytes += path.stat().st_size
                    path.unlink()
                    deleted_receipt_files += 1

        product_image_root = (self.data_dir / "product-images").resolve()
        deleted_product_image_files = 0
        deleted_product_image_bytes = 0
        if product_image_root.is_dir():
            for path in product_image_root.iterdir():
                if path.is_file():
                    deleted_product_image_bytes += path.stat().st_size
                    path.unlink()
                    deleted_product_image_files += 1

        table_order = (
            "notification_deliveries", "notification_events", "push_subscriptions",
            "notification_preferences", "api_tokens", "webauthn_challenges",
            "login_challenges", "recovery_codes", "totp_credentials",
            "webauthn_credentials", "auth_sessions", "household_invitations",
            "household_budget_settings", "shopping_generation_items",
            "shopping_generation_runs", "stock_count_lines", "stock_count_sessions",
            "stock_movements", "stock_lots", "shopping_list_items", "import_runs",
            "receipt_items", "receipts", "scan_drafts", "catalog_barcodes",
            "catalog_external_refs", "catalog_product_variants", "catalog_aliases",
            "catalog_product_mappings", "catalog_products", "catalog_locations",
            "catalog_quantity_units", "catalog_product_groups", "product_aliases",
            "product_mappings", "household_memberships", "users", "households",
            "auth_attempts", "audit_events", "app_settings",
        )
        with self.database.connect() as conn:
            for table in table_order:
                # table_order is the fixed installation-erasure allow-list above.
                conn.execute(f"DELETE FROM {table}")  # nosec B608
        self.database.initialize()
        return {
            "deleted": True,
            "deleted_receipt_files": deleted_receipt_files,
            "deleted_receipt_bytes": deleted_receipt_bytes,
            "deleted_product_image_files": deleted_product_image_files,
            "deleted_product_image_bytes": deleted_product_image_bytes,
            "completed_at": now_iso(),
        }
