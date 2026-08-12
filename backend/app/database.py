from __future__ import annotations

import json
import hashlib
import calendar
import re
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

from .services.receipt_identity import build_receipt_fingerprint


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


def _shift_month(value: date, offset: int) -> date:
    absolute = value.year * 12 + value.month - 1 + offset
    return date(absolute // 12, absolute % 12 + 1, 1)


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS households (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    email TEXT COLLATE NOCASE UNIQUE,
                    password_hash TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    owner_setup_complete INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS household_memberships (
                    id TEXT PRIMARY KEY,
                    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK(role IN ('owner', 'admin', 'member', 'viewer')),
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(household_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS auth_sessions (
                    id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL UNIQUE,
                    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    device_name TEXT NOT NULL,
                    source_hash TEXT,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS household_invitations (
                    id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL UNIQUE,
                    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    invited_by_user_id TEXT NOT NULL REFERENCES users(id),
                    display_name TEXT NOT NULL,
                    email TEXT NOT NULL COLLATE NOCASE,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'member', 'viewer')),
                    expires_at TEXT NOT NULL,
                    accepted_at TEXT,
                    revoked_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS webauthn_credentials (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    credential_id BLOB NOT NULL UNIQUE,
                    public_key BLOB NOT NULL,
                    sign_count INTEGER NOT NULL DEFAULT 0,
                    device_type TEXT NOT NULL,
                    backed_up INTEGER NOT NULL DEFAULT 0,
                    transports_json TEXT NOT NULL DEFAULT '[]',
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT
                );

                CREATE TABLE IF NOT EXISTS webauthn_challenges (
                    id TEXT PRIMARY KEY,
                    challenge BLOB NOT NULL,
                    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    session_id TEXT REFERENCES auth_sessions(id) ON DELETE CASCADE,
                    ceremony TEXT NOT NULL CHECK(ceremony IN ('registration', 'authentication')),
                    purpose TEXT NOT NULL CHECK(purpose IN ('login', 'registration', 'reauthentication')),
                    rp_id TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS totp_credentials (
                    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    secret_encrypted TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    last_used_step INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS recovery_codes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    code_hash TEXT NOT NULL UNIQUE,
                    used_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS login_challenges (
                    id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    source_hash TEXT,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS api_tokens (
                    id TEXT PRIMARY KEY,
                    token_prefix TEXT NOT NULL UNIQUE,
                    token_hash TEXT NOT NULL UNIQUE,
                    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    scopes_json TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    revoked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS notification_preferences (
                    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    push_enabled INTEGER NOT NULL DEFAULT 0,
                    low_stock_enabled INTEGER NOT NULL DEFAULT 1,
                    expiry_enabled INTEGER NOT NULL DEFAULT 1,
                    expiry_days_before INTEGER NOT NULL DEFAULT 7,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id TEXT PRIMARY KEY,
                    endpoint_hash TEXT NOT NULL UNIQUE,
                    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    subscription_encrypted TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_success_at TEXT,
                    last_failure_at TEXT,
                    revoked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS notification_events (
                    id TEXT PRIMARY KEY,
                    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL CHECK(kind IN ('low_stock', 'expiry')),
                    subject_id TEXT NOT NULL,
                    condition_key TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    last_notified_at TEXT,
                    resolved_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, kind, subject_id)
                );

                CREATE TABLE IF NOT EXISTS notification_deliveries (
                    id TEXT PRIMARY KEY,
                    event_id TEXT REFERENCES notification_events(id) ON DELETE SET NULL,
                    subscription_id TEXT REFERENCES push_subscriptions(id) ON DELETE SET NULL,
                    household_id TEXT NOT NULL REFERENCES households(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL,
                    outcome TEXT NOT NULL CHECK(outcome IN ('success', 'failure')),
                    status_code INTEGER,
                    error TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS household_budget_settings (
                    household_id TEXT PRIMARY KEY REFERENCES households(id) ON DELETE CASCADE,
                    monthly_limit_cents INTEGER NOT NULL CHECK(monthly_limit_cents > 0),
                    currency TEXT NOT NULL DEFAULT 'EUR',
                    warning_percent INTEGER NOT NULL DEFAULT 80
                        CHECK(warning_percent BETWEEN 50 AND 100),
                    updated_by_user_id TEXT NOT NULL REFERENCES users(id),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS receipts (
                    id TEXT PRIMARY KEY,
                    store_name TEXT,
                    purchase_date TEXT,
                    currency TEXT NOT NULL DEFAULT 'EUR',
                    total REAL,
                    status TEXT NOT NULL,
                    image_path TEXT,
                    source_sha256 TEXT,
                    receipt_fingerprint TEXT,
                    analysis_version TEXT,
                    retailer TEXT,
                    store_number TEXT,
                    store_address TEXT,
                    grocy_store_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS receipt_items (
                    id TEXT PRIMARY KEY,
                    receipt_id TEXT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
                    position INTEGER NOT NULL,
                    raw_name TEXT NOT NULL,
                    normalized_name TEXT,
                    quantity REAL NOT NULL DEFAULT 1,
                    unit_price REAL,
                    total_price REAL,
                    barcode TEXT,
                    brand TEXT,
                    best_before_date TEXT,
                    suggested_location TEXT,
                    suggested_unit TEXT,
                    suggested_product_group TEXT,
                    suggested_best_before_days INTEGER,
                    suggestion_confidence REAL,
                    catalog_variant_id TEXT,
                    match_reason TEXT,
                    match_evidence_json TEXT NOT NULL DEFAULT '[]',
                    grocy_product_id INTEGER,
                    grocy_product_name TEXT,
                    match_status TEXT NOT NULL DEFAULT 'unresolved',
                    match_score REAL,
                    suggested_product_id INTEGER,
                    suggested_product_name TEXT,
                    suggested_product_score REAL,
                    imported INTEGER NOT NULL DEFAULT 0,
                    import_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS product_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_key TEXT NOT NULL,
                    raw_key TEXT NOT NULL,
                    grocy_product_id INTEGER NOT NULL,
                    grocy_product_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(store_key, raw_key)
                );

                CREATE TABLE IF NOT EXISTS import_runs (
                    id TEXT PRIMARY KEY,
                    receipt_id TEXT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
                    requested_count INTEGER NOT NULL,
                    imported_count INTEGER NOT NULL,
                    failed_count INTEGER NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS product_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias_key TEXT NOT NULL,
                    grocy_product_id INTEGER NOT NULL,
                    grocy_product_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(alias_key, grocy_product_id)
                );

                CREATE TABLE IF NOT EXISTS catalog_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    is_freezer INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    grocy_id INTEGER UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS catalog_quantity_units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    name_plural TEXT,
                    description TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1,
                    grocy_id INTEGER UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS catalog_product_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1,
                    grocy_id INTEGER UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS catalog_products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL UNIQUE,
                    product_group_id INTEGER REFERENCES catalog_product_groups(id),
                    default_location_id INTEGER REFERENCES catalog_locations(id),
                    default_quantity_unit_id INTEGER REFERENCES catalog_quantity_units(id),
                    default_best_before_days INTEGER NOT NULL DEFAULT 0,
                    minimum_stock_quantity REAL NOT NULL DEFAULT 0,
                    shopping_target_quantity REAL NOT NULL DEFAULT 0,
                    image_url TEXT,
                    notes TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS catalog_product_variants (
                    id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL REFERENCES catalog_products(id) ON DELETE CASCADE,
                    name TEXT,
                    brand TEXT,
                    package_amount REAL,
                    package_unit TEXT,
                    image_url TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS catalog_barcodes (
                    barcode TEXT PRIMARY KEY,
                    variant_id TEXT NOT NULL REFERENCES catalog_product_variants(id) ON DELETE CASCADE,
                    symbology TEXT,
                    is_primary INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS catalog_external_refs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    product_id TEXT REFERENCES catalog_products(id) ON DELETE CASCADE,
                    variant_id TEXT REFERENCES catalog_product_variants(id) ON DELETE CASCADE,
                    source_url TEXT,
                    license TEXT,
                    attribution TEXT,
                    payload_json TEXT,
                    fetched_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(source, external_id)
                );

                CREATE TABLE IF NOT EXISTS catalog_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias_key TEXT NOT NULL,
                    product_id TEXT NOT NULL REFERENCES catalog_products(id) ON DELETE CASCADE,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(alias_key, product_id)
                );

                CREATE TABLE IF NOT EXISTS catalog_product_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_key TEXT NOT NULL,
                    raw_key TEXT NOT NULL,
                    product_id TEXT NOT NULL REFERENCES catalog_products(id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(store_key, raw_key)
                );

                CREATE TABLE IF NOT EXISTS stock_lots (
                    id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL REFERENCES catalog_products(id),
                    variant_id TEXT REFERENCES catalog_product_variants(id),
                    location_id INTEGER REFERENCES catalog_locations(id),
                    quantity REAL NOT NULL,
                    best_before_date TEXT,
                    unit_price REAL,
                    purchased_date TEXT,
                    receipt_item_id TEXT UNIQUE REFERENCES receipt_items(id),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS stock_movements (
                    id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL REFERENCES catalog_products(id),
                    variant_id TEXT REFERENCES catalog_product_variants(id),
                    lot_id TEXT REFERENCES stock_lots(id),
                    location_id INTEGER REFERENCES catalog_locations(id),
                    movement_type TEXT NOT NULL,
                    quantity_delta REAL NOT NULL,
                    source TEXT NOT NULL,
                    reference_id TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS stock_count_sessions (
                    id TEXT PRIMARY KEY,
                    client_mutation_id TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'confirmed',
                    line_count INTEGER NOT NULL DEFAULT 0,
                    changed_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS stock_count_lines (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES stock_count_sessions(id) ON DELETE CASCADE,
                    product_id TEXT NOT NULL REFERENCES catalog_products(id),
                    variant_id TEXT REFERENCES catalog_product_variants(id),
                    location_id INTEGER REFERENCES catalog_locations(id),
                    previous_quantity REAL NOT NULL,
                    counted_quantity REAL NOT NULL,
                    quantity_delta REAL NOT NULL,
                    best_before_date TEXT,
                    unit_price REAL,
                    note TEXT NOT NULL DEFAULT '',
                    movement_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(session_id, product_id)
                );

                CREATE TABLE IF NOT EXISTS shopping_list_items (
                    id TEXT PRIMARY KEY,
                    product_id TEXT REFERENCES catalog_products(id),
                    label TEXT NOT NULL,
                    desired_quantity REAL NOT NULL DEFAULT 1,
                    checked INTEGER NOT NULL DEFAULT 0,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS shopping_generation_runs (
                    id TEXT PRIMARY KEY,
                    client_mutation_id TEXT NOT NULL UNIQUE,
                    requested_count INTEGER NOT NULL DEFAULT 0,
                    created_count INTEGER NOT NULL DEFAULT 0,
                    updated_count INTEGER NOT NULL DEFAULT 0,
                    unchanged_count INTEGER NOT NULL DEFAULT 0,
                    skipped_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS shopping_generation_items (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES shopping_generation_runs(id) ON DELETE CASCADE,
                    product_id TEXT NOT NULL REFERENCES catalog_products(id),
                    shopping_item_id TEXT REFERENCES shopping_list_items(id),
                    current_quantity REAL NOT NULL,
                    minimum_quantity REAL NOT NULL,
                    target_quantity REAL NOT NULL,
                    suggested_quantity REAL NOT NULL,
                    action TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(run_id, product_id)
                );

                CREATE TABLE IF NOT EXISTS scan_drafts (
                    id TEXT PRIMARY KEY,
                    barcode_raw TEXT NOT NULL,
                    barcode_normalized TEXT NOT NULL,
                    symbology TEXT,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    resolution_source TEXT NOT NULL,
                    product_id TEXT REFERENCES catalog_products(id),
                    variant_id TEXT REFERENCES catalog_product_variants(id),
                    proposed_json TEXT NOT NULL DEFAULT '{}',
                    upstream_error TEXT,
                    resolve_key TEXT,
                    confirmation_key TEXT,
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS auth_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_hash TEXT NOT NULL,
                    failed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    source_hash TEXT,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt
                    ON receipt_items(receipt_id, position);
                CREATE INDEX IF NOT EXISTS idx_mappings_lookup
                    ON product_mappings(store_key, raw_key);
                CREATE INDEX IF NOT EXISTS idx_aliases_lookup
                    ON product_aliases(alias_key);
                CREATE INDEX IF NOT EXISTS idx_catalog_products_name
                    ON catalog_products(normalized_name);
                CREATE INDEX IF NOT EXISTS idx_catalog_aliases_lookup
                    ON catalog_aliases(alias_key);
                CREATE INDEX IF NOT EXISTS idx_catalog_mappings_lookup
                    ON catalog_product_mappings(store_key, raw_key);
                CREATE INDEX IF NOT EXISTS idx_stock_product
                    ON stock_lots(product_id);
                CREATE INDEX IF NOT EXISTS idx_stock_count_sessions_created
                    ON stock_count_sessions(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_stock_count_lines_session
                    ON stock_count_lines(session_id);
                CREATE INDEX IF NOT EXISTS idx_shopping_generation_runs_created
                    ON shopping_generation_runs(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_shopping_generation_items_run
                    ON shopping_generation_items(run_id);
                CREATE INDEX IF NOT EXISTS idx_scan_drafts_status
                    ON scan_drafts(status, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_scan_drafts_barcode
                    ON scan_drafts(barcode_normalized, status);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_scan_drafts_resolve_key
                    ON scan_drafts(resolve_key) WHERE resolve_key IS NOT NULL;
                CREATE UNIQUE INDEX IF NOT EXISTS idx_scan_drafts_confirmation_key
                    ON scan_drafts(confirmation_key) WHERE confirmation_key IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_auth_attempts_source_time
                    ON auth_attempts(source_hash, failed_at);
                CREATE INDEX IF NOT EXISTS idx_audit_events_created
                    ON audit_events(created_at);
                CREATE INDEX IF NOT EXISTS idx_memberships_user
                    ON household_memberships(user_id, active);
                CREATE INDEX IF NOT EXISTS idx_auth_sessions_user
                    ON auth_sessions(user_id, revoked_at, last_seen_at DESC);
                CREATE INDEX IF NOT EXISTS idx_auth_sessions_token
                    ON auth_sessions(token_hash);
                CREATE INDEX IF NOT EXISTS idx_household_invitations_active
                    ON household_invitations(household_id, accepted_at, revoked_at, expires_at);
                CREATE INDEX IF NOT EXISTS idx_webauthn_credentials_user
                    ON webauthn_credentials(user_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_webauthn_challenges_expiry
                    ON webauthn_challenges(expires_at, used_at);
                CREATE INDEX IF NOT EXISTS idx_recovery_codes_user
                    ON recovery_codes(user_id, used_at);
                CREATE INDEX IF NOT EXISTS idx_login_challenges_token
                    ON login_challenges(token_hash, expires_at, used_at);
                CREATE INDEX IF NOT EXISTS idx_api_tokens_user
                    ON api_tokens(user_id, revoked_at, expires_at);
                CREATE INDEX IF NOT EXISTS idx_api_tokens_hash
                    ON api_tokens(token_hash);
                CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user
                    ON push_subscriptions(user_id, active, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_notification_events_user
                    ON notification_events(user_id, active, kind);
                CREATE INDEX IF NOT EXISTS idx_notification_deliveries_created
                    ON notification_deliveries(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_receipts_budget_date
                    ON receipts(purchase_date, status, currency);
                """
            )
            self._ensure_columns(conn)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_receipts_fingerprint "
                "ON receipts(receipt_fingerprint)"
            )
            self._demote_unconfirmed_fuzzy_matches(conn)
            self._backfill_receipt_hashes(conn)
            self._backfill_receipt_fingerprints(conn)
            self._backfill_aliases(conn)
            self._seed_catalog_master_data(conn)
            self._backfill_catalog(conn)

    def _ensure_columns(self, conn: sqlite3.Connection) -> None:
        columns: dict[str, dict[str, str]] = {
            "receipts": {
                "source_sha256": "TEXT",
                "receipt_fingerprint": "TEXT",
                "analysis_version": "TEXT",
                "retailer": "TEXT",
                "store_number": "TEXT",
                "store_address": "TEXT",
            },
            "receipt_items": {
                "brand": "TEXT",
                "best_before_date": "TEXT",
                "suggested_location": "TEXT",
                "suggested_unit": "TEXT",
                "suggested_product_group": "TEXT",
                "suggested_best_before_days": "INTEGER",
                "suggestion_confidence": "REAL",
                "catalog_variant_id": "TEXT",
                "match_reason": "TEXT",
                "match_evidence_json": "TEXT NOT NULL DEFAULT '[]'",
                "suggested_product_id": "INTEGER",
                "suggested_product_name": "TEXT",
                "suggested_product_score": "REAL",
                "catalog_product_id": "TEXT",
                "catalog_product_name": "TEXT",
                "suggested_catalog_product_id": "TEXT",
                "suggested_catalog_product_name": "TEXT",
                "suggested_catalog_product_score": "REAL",
                "grocy_exported": "INTEGER NOT NULL DEFAULT 0",
            },
            "stock_lots": {
                "opened_at": "TEXT",
            },
            "catalog_products": {
                "minimum_stock_quantity": "REAL NOT NULL DEFAULT 0",
                "shopping_target_quantity": "REAL NOT NULL DEFAULT 0",
            },
            "auth_sessions": {
                "authenticated_at": "TEXT",
                "authentication_method": "TEXT NOT NULL DEFAULT 'password'",
            },
        }
        for table, expected in columns.items():
            existing = {
                str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})")
            }
            for name, definition in expected.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
        conn.execute(
            "UPDATE auth_sessions SET authenticated_at = created_at WHERE authenticated_at IS NULL"
        )

    def _backfill_receipt_fingerprints(self, conn: sqlite3.Connection) -> None:
        receipts = conn.execute(
            "SELECT * FROM receipts WHERE receipt_fingerprint IS NULL"
        ).fetchall()
        for receipt in receipts:
            items = conn.execute(
                "SELECT * FROM receipt_items WHERE receipt_id = ? ORDER BY position",
                (receipt["id"],),
            ).fetchall()
            fingerprint = build_receipt_fingerprint(
                dict(receipt), [dict(item) for item in items]
            )
            if fingerprint:
                conn.execute(
                    "UPDATE receipts SET receipt_fingerprint = ? WHERE id = ?",
                    (fingerprint, receipt["id"]),
                )

    def _backfill_receipt_hashes(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            "SELECT id, image_path FROM receipts WHERE source_sha256 IS NULL AND image_path IS NOT NULL"
        ).fetchall()
        for row in rows:
            path = Path(str(row["image_path"]))
            if path.is_file():
                conn.execute(
                    "UPDATE receipts SET source_sha256 = ? WHERE id = ?",
                    (hashlib.sha256(path.read_bytes()).hexdigest(), row["id"]),
                )

    def _demote_unconfirmed_fuzzy_matches(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            UPDATE receipt_items
            SET suggested_product_id = grocy_product_id,
                suggested_product_name = grocy_product_name,
                suggested_product_score = match_score,
                grocy_product_id = NULL,
                grocy_product_name = NULL,
                match_status = 'suggested',
                match_score = NULL,
                updated_at = ?
            WHERE match_status = 'fuzzy' AND imported = 0
            """,
            (now_iso(),),
        )

    def _backfill_aliases(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            """
            SELECT raw_name, normalized_name, grocy_product_id, grocy_product_name
            FROM receipt_items
            WHERE grocy_product_id IS NOT NULL
              AND grocy_product_name IS NOT NULL
              AND match_status IN ('manual', 'learned', 'exact', 'barcode')
            """
        ).fetchall()
        for row in rows:
            self._remember_aliases(
                conn,
                str(row["raw_name"]),
                str(row["normalized_name"] or ""),
                int(row["grocy_product_id"]),
                str(row["grocy_product_name"]),
                "backfill",
            )

    def _seed_catalog_master_data(self, conn: sqlite3.Connection) -> None:
        timestamp = now_iso()
        locations = (
            ("Vorratskammer", "Trockenvorräte und haltbare Lebensmittel", 0),
            ("Kühlschrank", "Gekühlte Lebensmittel", 0),
            ("Tiefkühler", "Gefrierfach und Tiefkühlvorräte", 1),
            ("Badezimmer", "Pflege- und Hygieneprodukte", 0),
        )
        for name, description, is_freezer in locations:
            conn.execute(
                """
                INSERT INTO catalog_locations(
                    name, description, is_freezer, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO NOTHING
                """,
                (name, description, is_freezer, timestamp, timestamp),
            )

        units = (
            ("Stück", "Stück"),
            ("Packung", "Packungen"),
            ("Flasche", "Flaschen"),
            ("Dose", "Dosen"),
            ("Becher", "Becher"),
            ("Kilogramm", "Kilogramm"),
        )
        for name, plural in units:
            conn.execute(
                """
                INSERT INTO catalog_quantity_units(
                    name, name_plural, created_at, updated_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO NOTHING
                """,
                (name, plural, timestamp, timestamp),
            )

        for name in (
            "Lebensmittel",
            "Getränke",
            "Kühlprodukte",
            "Tiefkühlprodukte",
            "Obst & Gemüse",
            "Haushalt & Pflege",
        ):
            conn.execute(
                """
                INSERT INTO catalog_product_groups(name, created_at, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO NOTHING
                """,
                (name, timestamp, timestamp),
            )

    def _backfill_catalog(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            """
            SELECT DISTINCT grocy_product_id, grocy_product_name
            FROM receipt_items
            WHERE grocy_product_id IS NOT NULL AND grocy_product_name IS NOT NULL
            """
        ).fetchall()
        for row in rows:
            product_id = self._ensure_catalog_product(
                conn,
                name=str(row["grocy_product_name"]),
                grocy_id=int(row["grocy_product_id"]),
            )
            conn.execute(
                """
                UPDATE receipt_items
                SET catalog_product_id = ?, catalog_product_name = ?,
                    grocy_exported = CASE WHEN imported = 1 THEN 1 ELSE grocy_exported END
                WHERE grocy_product_id = ? AND catalog_product_id IS NULL
                """,
                (product_id, str(row["grocy_product_name"]), int(row["grocy_product_id"])),
            )

        mapping_rows = conn.execute(
            """
            SELECT store_key, raw_key, grocy_product_id, grocy_product_name
            FROM product_mappings
            """
        ).fetchall()
        for row in mapping_rows:
            product_id = self._ensure_catalog_product(
                conn,
                name=str(row["grocy_product_name"]),
                grocy_id=int(row["grocy_product_id"]),
            )
            conn.execute(
                """
                INSERT INTO catalog_product_mappings(
                    store_key, raw_key, product_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(store_key, raw_key) DO UPDATE SET
                    product_id = excluded.product_id,
                    updated_at = excluded.updated_at
                """,
                (row["store_key"], row["raw_key"], product_id, now_iso(), now_iso()),
            )

        alias_rows = conn.execute(
            """
            SELECT alias_key, grocy_product_id, grocy_product_name, source
            FROM product_aliases
            """
        ).fetchall()
        for row in alias_rows:
            product_id = self._ensure_catalog_product(
                conn,
                name=str(row["grocy_product_name"]),
                grocy_id=int(row["grocy_product_id"]),
            )
            conn.execute(
                """
                INSERT INTO catalog_aliases(
                    alias_key, product_id, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(alias_key, product_id) DO NOTHING
                """,
                (row["alias_key"], product_id, row["source"], now_iso(), now_iso()),
            )

    def _ensure_catalog_product(
        self,
        conn: sqlite3.Connection,
        *,
        name: str,
        grocy_id: int | None = None,
        product_id: str | None = None,
        product_group_id: int | None = None,
        location_id: int | None = None,
        quantity_unit_id: int | None = None,
        default_best_before_days: int = 0,
    ) -> str:
        clean_name = " ".join(name.strip().split())
        normalized = normalize_key(clean_name)
        existing = None
        if grocy_id is not None:
            existing = conn.execute(
                """
                SELECT p.id
                FROM catalog_external_refs r
                JOIN catalog_products p ON p.id = r.product_id
                WHERE r.source = 'grocy' AND r.external_id = ?
                """,
                (str(grocy_id),),
            ).fetchone()
        if not existing:
            existing = conn.execute(
                "SELECT id FROM catalog_products WHERE normalized_name = ?",
                (normalized,),
            ).fetchone()
        if existing:
            resolved_id = str(existing["id"])
            conn.execute(
                """
                UPDATE catalog_products
                SET name = ?,
                    product_group_id = COALESCE(?, product_group_id),
                    default_location_id = COALESCE(?, default_location_id),
                    default_quantity_unit_id = COALESCE(?, default_quantity_unit_id),
                    default_best_before_days = CASE
                        WHEN ? > 0 THEN ? ELSE default_best_before_days END,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    clean_name,
                    product_group_id,
                    location_id,
                    quantity_unit_id,
                    default_best_before_days,
                    default_best_before_days,
                    now_iso(),
                    resolved_id,
                ),
            )
        else:
            resolved_id = product_id or str(uuid.uuid4())
            timestamp = now_iso()
            conn.execute(
                """
                INSERT INTO catalog_products(
                    id, name, normalized_name, product_group_id,
                    default_location_id, default_quantity_unit_id,
                    default_best_before_days, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resolved_id,
                    clean_name,
                    normalized,
                    product_group_id,
                    location_id,
                    quantity_unit_id,
                    default_best_before_days,
                    timestamp,
                    timestamp,
                ),
            )
        if grocy_id is not None:
            timestamp = now_iso()
            conn.execute(
                """
                INSERT INTO catalog_external_refs(
                    source, external_id, product_id, created_at, updated_at
                ) VALUES ('grocy', ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    product_id = excluded.product_id,
                    updated_at = excluded.updated_at
                """,
                (str(grocy_id), resolved_id, timestamp, timestamp),
            )
        return resolved_id

    def get_setting(self, key: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
        return str(row["value"]) if row else None

    def put_setting(self, key: str, value: str) -> None:
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_settings(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, timestamp),
            )

    def ensure_owner_identity(self, password_hash: str | None = None) -> dict[str, Any]:
        """Create the single-household owner boundary without changing domain data."""
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT u.id AS user_id, u.display_name, u.email, u.password_hash,
                       u.owner_setup_complete, h.id AS household_id, h.name AS household_name,
                       m.role
                FROM household_memberships m
                JOIN users u ON u.id = m.user_id
                JOIN households h ON h.id = m.household_id
                WHERE m.role = 'owner' AND m.active = 1 AND u.active = 1
                ORDER BY m.created_at
                LIMIT 1
                """
            ).fetchone()
            if row:
                if password_hash and not row["password_hash"]:
                    conn.execute(
                        "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                        (password_hash, now_iso(), row["user_id"]),
                    )
                    row = conn.execute(
                        """
                        SELECT u.id AS user_id, u.display_name, u.email, u.password_hash,
                               u.owner_setup_complete, h.id AS household_id, h.name AS household_name,
                               m.role
                        FROM household_memberships m
                        JOIN users u ON u.id = m.user_id
                        JOIN households h ON h.id = m.household_id
                        WHERE u.id = ? AND m.active = 1
                        LIMIT 1
                        """,
                        (row["user_id"],),
                    ).fetchone()
                return dict(row)

            timestamp = now_iso()
            household_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO households(id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (household_id, "Mein Haushalt", timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO users(
                    id, display_name, password_hash, owner_setup_complete, created_at, updated_at
                ) VALUES (?, ?, ?, 0, ?, ?)
                """,
                (user_id, "Owner einrichten", password_hash, timestamp, timestamp),
            )
            conn.execute(
                """
                INSERT INTO household_memberships(
                    id, household_id, user_id, role, created_at, updated_at
                ) VALUES (?, ?, ?, 'owner', ?, ?)
                """,
                (str(uuid.uuid4()), household_id, user_id, timestamp, timestamp),
            )
            return {
                "user_id": user_id,
                "display_name": "Owner einrichten",
                "email": None,
                "password_hash": password_hash,
                "owner_setup_complete": 0,
                "household_id": household_id,
                "household_name": "Mein Haushalt",
                "role": "owner",
            }

    def get_login_identity(self, identifier: str | None = None) -> dict[str, Any] | None:
        with self.connect() as conn:
            if identifier:
                row = conn.execute(
                    """
                    SELECT u.id AS user_id, u.display_name, u.email, u.password_hash,
                           u.owner_setup_complete, h.id AS household_id, h.name AS household_name,
                           m.role
                    FROM users u
                    JOIN household_memberships m ON m.user_id = u.id
                    JOIN households h ON h.id = m.household_id
                    WHERE u.active = 1 AND m.active = 1
                      AND lower(u.email) = lower(?)
                    LIMIT 1
                    """,
                    (identifier.strip(),),
                ).fetchone()
            else:
                rows = conn.execute(
                    """
                    SELECT u.id AS user_id, u.display_name, u.email, u.password_hash,
                           u.owner_setup_complete, h.id AS household_id, h.name AS household_name,
                           m.role
                    FROM users u
                    JOIN household_memberships m ON m.user_id = u.id
                    JOIN households h ON h.id = m.household_id
                    WHERE u.active = 1 AND m.active = 1
                    ORDER BY u.created_at
                    LIMIT 2
                    """
                ).fetchall()
                row = rows[0] if len(rows) == 1 else None
        return dict(row) if row else None

    def active_user_count(self) -> int:
        with self.connect() as conn:
            return int(
                conn.execute(
                    """
                    SELECT COUNT(DISTINCT u.id)
                    FROM users u
                    JOIN household_memberships m ON m.user_id = u.id
                    WHERE u.active = 1 AND m.active = 1
                    """
                ).fetchone()[0]
            )

    def update_owner_profile(
        self, user_id: str, *, display_name: str, email: str | None
    ) -> dict[str, Any] | None:
        clean_name = " ".join(display_name.strip().split())
        clean_email = email.strip().lower() if email and email.strip() else None
        with self.connect() as conn:
            membership = conn.execute(
                """
                SELECT household_id FROM household_memberships
                WHERE user_id = ? AND role = 'owner' AND active = 1
                """,
                (user_id,),
            ).fetchone()
            if not membership:
                return None
            conn.execute(
                """
                UPDATE users
                SET display_name = ?, email = ?, owner_setup_complete = 1, updated_at = ?
                WHERE id = ? AND active = 1
                """,
                (clean_name, clean_email, now_iso(), user_id),
            )
            row = conn.execute(
                """
                SELECT u.id AS user_id, u.display_name, u.email, u.owner_setup_complete,
                       h.id AS household_id, h.name AS household_name, m.role
                FROM users u
                JOIN household_memberships m ON m.user_id = u.id
                JOIN households h ON h.id = m.household_id
                WHERE u.id = ? AND m.active = 1
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _session_token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_auth_session(
        self,
        *,
        user_id: str,
        household_id: str,
        device_name: str,
        source_hash: str | None,
        max_age_seconds: int,
        authentication_method: str = "password",
    ) -> tuple[dict[str, Any], str]:
        token = secrets.token_urlsafe(32)
        timestamp = now_iso()
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=max_age_seconds)
        ).isoformat(timespec="microseconds")
        session_id = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_sessions(
                    id, token_hash, household_id, user_id, device_name, source_hash,
                    created_at, last_seen_at, expires_at, authenticated_at,
                    authentication_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self._session_token_hash(token),
                    household_id,
                    user_id,
                    device_name[:120],
                    source_hash,
                    timestamp,
                    timestamp,
                    expires_at,
                    timestamp,
                    authentication_method,
                ),
            )
        return {
            "id": session_id,
            "user_id": user_id,
            "household_id": household_id,
            "device_name": device_name[:120],
            "created_at": timestamp,
            "last_seen_at": timestamp,
            "expires_at": expires_at,
            "authenticated_at": timestamp,
            "authentication_method": authentication_method,
        }, token

    def resolve_auth_session(self, token: str, *, touch: bool = True) -> dict[str, Any] | None:
        token_hash = self._session_token_hash(token)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT s.id AS session_id, s.device_name, s.created_at,
                       s.last_seen_at, s.expires_at, s.authenticated_at,
                       s.authentication_method, u.id AS user_id,
                       u.display_name, u.email, u.owner_setup_complete,
                       h.id AS household_id, h.name AS household_name, m.role
                FROM auth_sessions s
                JOIN users u ON u.id = s.user_id
                JOIN households h ON h.id = s.household_id
                JOIN household_memberships m
                  ON m.user_id = u.id AND m.household_id = h.id
                WHERE s.token_hash = ? AND s.revoked_at IS NULL
                  AND u.active = 1 AND m.active = 1
                LIMIT 1
                """,
                (token_hash,),
            ).fetchone()
            if not row:
                return None
            if datetime.fromisoformat(str(row["expires_at"])) <= datetime.now(UTC):
                conn.execute(
                    "UPDATE auth_sessions SET revoked_at = ? WHERE id = ?",
                    (now_iso(), row["session_id"]),
                )
                return None
            resolved = dict(row)
            if touch:
                last_seen = datetime.fromisoformat(str(row["last_seen_at"]))
                if datetime.now(UTC) - last_seen >= timedelta(minutes=5):
                    resolved["last_seen_at"] = now_iso()
                    conn.execute(
                        "UPDATE auth_sessions SET last_seen_at = ? WHERE id = ?",
                        (resolved["last_seen_at"], row["session_id"]),
                    )
        return resolved

    def list_auth_sessions(self, user_id: str, current_token: str) -> list[dict[str, Any]]:
        current_hash = self._session_token_hash(current_token)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, token_hash, device_name, created_at, last_seen_at, expires_at,
                       authenticated_at, authentication_method
                FROM auth_sessions
                WHERE user_id = ? AND revoked_at IS NULL AND expires_at > ?
                ORDER BY last_seen_at DESC, created_at DESC
                """,
                (user_id, now_iso()),
            ).fetchall()
        return [
            {
                "id": str(row["id"]),
                "device_name": str(row["device_name"]),
                "created_at": str(row["created_at"]),
                "last_seen_at": str(row["last_seen_at"]),
                "expires_at": str(row["expires_at"]),
                "authenticated_at": str(row["authenticated_at"]),
                "authentication_method": str(row["authentication_method"]),
                "current": secrets.compare_digest(str(row["token_hash"]), current_hash),
            }
            for row in rows
        ]

    def revoke_auth_session(self, user_id: str, session_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE auth_sessions SET revoked_at = ?
                WHERE id = ? AND user_id = ? AND revoked_at IS NULL
                """,
                (now_iso(), session_id, user_id),
            )
        return cursor.rowcount > 0

    def revoke_auth_token(self, token: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE auth_sessions SET revoked_at = ?
                WHERE token_hash = ? AND revoked_at IS NULL
                """,
                (now_iso(), self._session_token_hash(token)),
            )
        return cursor.rowcount > 0

    def revoke_other_auth_sessions(self, user_id: str, current_token: str) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE auth_sessions SET revoked_at = ?
                WHERE user_id = ? AND token_hash != ? AND revoked_at IS NULL
                """,
                (now_iso(), user_id, self._session_token_hash(current_token)),
            )
        return max(0, cursor.rowcount)

    @staticmethod
    def _api_token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _api_token_public(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        value = dict(row)
        try:
            scopes = json.loads(str(value.get("scopes_json") or "[]"))
        except json.JSONDecodeError:
            scopes = []
        return {
            "id": str(value["id"]),
            "name": str(value["name"]),
            "token_prefix": str(value["token_prefix"]),
            "scopes": scopes if isinstance(scopes, list) else [],
            "expires_at": str(value["expires_at"]),
            "created_at": str(value["created_at"]),
            "last_used_at": value.get("last_used_at"),
        }

    def create_api_token(
        self,
        *,
        user_id: str,
        household_id: str,
        name: str,
        scopes: list[str],
        expires_days: int,
    ) -> tuple[dict[str, Any], str]:
        timestamp = now_iso()
        expires_at = (
            datetime.now(UTC) + timedelta(days=expires_days)
        ).isoformat(timespec="microseconds")
        token_id = str(uuid.uuid4())
        with self.connect() as conn:
            while True:
                prefix = secrets.token_urlsafe(6)
                if not conn.execute(
                    "SELECT 1 FROM api_tokens WHERE token_prefix = ?", (prefix,)
                ).fetchone():
                    break
            raw_token = f"vor_pat_{prefix}_{secrets.token_urlsafe(32)}"
            conn.execute(
                """
                INSERT INTO api_tokens(
                    id, token_prefix, token_hash, household_id, user_id, name,
                    scopes_json, expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    token_id,
                    prefix,
                    self._api_token_hash(raw_token),
                    household_id,
                    user_id,
                    " ".join(name.strip().split())[:100],
                    json.dumps(sorted(set(scopes)), separators=(",", ":")),
                    expires_at,
                    timestamp,
                ),
            )
            row = conn.execute(
                """
                SELECT id, name, token_prefix, scopes_json, expires_at,
                       created_at, last_used_at
                FROM api_tokens WHERE id = ?
                """,
                (token_id,),
            ).fetchone()
        return self._api_token_public(row), raw_token

    def list_api_tokens(self, user_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, token_prefix, scopes_json, expires_at,
                       created_at, last_used_at
                FROM api_tokens
                WHERE user_id = ? AND revoked_at IS NULL AND expires_at > ?
                ORDER BY created_at DESC
                """,
                (user_id, now_iso()),
            ).fetchall()
        return [self._api_token_public(row) for row in rows]

    def resolve_api_token(self, token: str, *, touch: bool = True) -> dict[str, Any] | None:
        token_hash = self._api_token_hash(token)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT t.id AS api_token_id, t.name AS api_token_name,
                       t.scopes_json, t.created_at AS token_created_at,
                       t.last_used_at, t.expires_at,
                       u.id AS user_id, u.display_name, u.email,
                       u.owner_setup_complete, h.id AS household_id,
                       h.name AS household_name, m.role
                FROM api_tokens t
                JOIN users u ON u.id = t.user_id
                JOIN households h ON h.id = t.household_id
                JOIN household_memberships m
                  ON m.user_id = u.id AND m.household_id = h.id
                WHERE t.token_hash = ? AND t.revoked_at IS NULL
                  AND t.expires_at > ? AND u.active = 1 AND m.active = 1
                LIMIT 1
                """,
                (token_hash, now_iso()),
            ).fetchone()
            if not row:
                return None
            resolved = dict(row)
            try:
                scopes = json.loads(str(resolved.pop("scopes_json") or "[]"))
            except json.JSONDecodeError:
                scopes = []
            resolved["api_token_scopes"] = scopes if isinstance(scopes, list) else []
            if touch:
                last_used = resolved.get("last_used_at")
                if not last_used or datetime.now(UTC) - datetime.fromisoformat(
                    str(last_used)
                ) >= timedelta(minutes=5):
                    resolved["last_used_at"] = now_iso()
                    conn.execute(
                        "UPDATE api_tokens SET last_used_at = ? WHERE id = ?",
                        (resolved["last_used_at"], resolved["api_token_id"]),
                    )
        return resolved

    def revoke_api_token_for_user(self, user_id: str, token_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE api_tokens SET revoked_at = ?
                WHERE id = ? AND user_id = ? AND revoked_at IS NULL
                """,
                (now_iso(), token_id, user_id),
            )
        return cursor.rowcount > 0

    def mark_session_reauthenticated(self, session_id: str, method: str) -> bool:
        timestamp = now_iso()
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE auth_sessions
                SET authenticated_at = ?, authentication_method = ?
                WHERE id = ? AND revoked_at IS NULL AND expires_at > ?
                """,
                (timestamp, method, session_id, timestamp),
            )
        return cursor.rowcount > 0

    def mark_session_authentication_stale(self, session_id: str, method: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE auth_sessions
                SET authenticated_at = '1970-01-01T00:00:00+00:00',
                    authentication_method = ?
                WHERE id = ?
                """,
                (method, session_id),
            )

    def update_password(self, user_id: str, password_hash: str, current_session_id: str) -> bool:
        timestamp = now_iso()
        with self.connect() as conn:
            cursor = conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ? AND active = 1",
                (password_hash, timestamp, user_id),
            )
            if cursor.rowcount:
                conn.execute(
                    """
                    UPDATE auth_sessions SET revoked_at = ?
                    WHERE user_id = ? AND id != ? AND revoked_at IS NULL
                    """,
                    (timestamp, user_id, current_session_id),
                )
        return cursor.rowcount > 0

    def get_identity_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT u.id AS user_id, u.display_name, u.email, u.password_hash,
                       u.owner_setup_complete, h.id AS household_id,
                       h.name AS household_name, m.role
                FROM users u
                JOIN household_memberships m ON m.user_id = u.id
                JOIN households h ON h.id = m.household_id
                WHERE u.id = ? AND u.active = 1 AND m.active = 1
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def create_login_challenge(
        self, user_id: str, source_hash: str | None, expires_seconds: int = 300
    ) -> str:
        token = secrets.token_urlsafe(32)
        timestamp = now_iso()
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=expires_seconds)
        ).isoformat(timespec="microseconds")
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM login_challenges WHERE expires_at <= ? OR used_at IS NOT NULL",
                (timestamp,),
            )
            conn.execute(
                """
                INSERT INTO login_challenges(
                    id, token_hash, user_id, source_hash, expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    self._session_token_hash(token),
                    user_id,
                    source_hash,
                    expires_at,
                    timestamp,
                ),
            )
        return token

    def resolve_login_challenge(
        self, token: str, source_hash: str | None
    ) -> dict[str, Any] | None:
        token_hash = self._session_token_hash(token)
        timestamp = now_iso()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, source_hash FROM login_challenges
                WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?
                LIMIT 1
                """,
                (token_hash, timestamp),
            ).fetchone()
            if not row or (row["source_hash"] and row["source_hash"] != source_hash):
                return None
            identity = conn.execute(
                """
                SELECT u.id AS user_id, u.display_name, u.email, u.password_hash,
                       u.owner_setup_complete, h.id AS household_id,
                       h.name AS household_name, m.role
                FROM users u
                JOIN household_memberships m ON m.user_id = u.id
                JOIN households h ON h.id = m.household_id
                WHERE u.id = ? AND u.active = 1 AND m.active = 1
                LIMIT 1
                """,
                (row["user_id"],),
            ).fetchone()
        return dict(identity) if identity else None

    def consume_login_challenge(self, token: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE login_challenges SET used_at = ?
                WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?
                """,
                (now_iso(), self._session_token_hash(token), now_iso()),
            )
        return cursor.rowcount > 0

    def list_household_members(self, household_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT u.id, u.display_name, u.email, u.active, m.role,
                       u.created_at, u.updated_at,
                       COUNT(CASE
                           WHEN s.revoked_at IS NULL AND s.expires_at > ? THEN 1
                       END) AS active_session_count
                FROM household_memberships m
                JOIN users u ON u.id = m.user_id
                LEFT JOIN auth_sessions s ON s.user_id = u.id
                WHERE m.household_id = ?
                GROUP BY u.id, u.display_name, u.email, u.active, m.role,
                         u.created_at, u.updated_at
                ORDER BY CASE m.role
                    WHEN 'owner' THEN 0 WHEN 'admin' THEN 1
                    WHEN 'member' THEN 2 ELSE 3 END,
                    lower(u.display_name)
                """,
                (now_iso(), household_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_household_invitation(
        self,
        *,
        household_id: str,
        invited_by_user_id: str,
        display_name: str,
        email: str,
        role: str,
        expires_hours: int,
    ) -> tuple[dict[str, Any], str]:
        token = secrets.token_urlsafe(32)
        token_hash = self._session_token_hash(token)
        clean_name = " ".join(display_name.strip().split())
        clean_email = email.strip().lower()
        timestamp = now_iso()
        expires_at = (
            datetime.now(UTC) + timedelta(hours=expires_hours)
        ).isoformat(timespec="microseconds")
        invitation_id = str(uuid.uuid4())
        with self.connect() as conn:
            existing_user = conn.execute(
                "SELECT id FROM users WHERE lower(email) = lower(?)",
                (clean_email,),
            ).fetchone()
            if existing_user:
                raise ValueError("member_exists")
            existing_invite = conn.execute(
                """
                SELECT id FROM household_invitations
                WHERE household_id = ? AND lower(email) = lower(?)
                  AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at > ?
                """,
                (household_id, clean_email, timestamp),
            ).fetchone()
            if existing_invite:
                raise ValueError("invitation_exists")
            conn.execute(
                """
                INSERT INTO household_invitations(
                    id, token_hash, household_id, invited_by_user_id,
                    display_name, email, role, expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invitation_id,
                    token_hash,
                    household_id,
                    invited_by_user_id,
                    clean_name,
                    clean_email,
                    role,
                    expires_at,
                    timestamp,
                ),
            )
        return {
            "id": invitation_id,
            "display_name": clean_name,
            "email": clean_email,
            "role": role,
            "expires_at": expires_at,
            "created_at": timestamp,
        }, token

    def get_household_invitation(self, token: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT i.id, i.household_id, h.name AS household_name,
                       i.display_name, i.email, i.role, i.expires_at,
                       i.accepted_at, i.revoked_at, i.created_at
                FROM household_invitations i
                JOIN households h ON h.id = i.household_id
                WHERE i.token_hash = ?
                LIMIT 1
                """,
                (self._session_token_hash(token),),
            ).fetchone()
        if not row:
            return None
        invitation = dict(row)
        invitation["valid"] = bool(
            not invitation["accepted_at"]
            and not invitation["revoked_at"]
            and datetime.fromisoformat(str(invitation["expires_at"])) > datetime.now(UTC)
        )
        return invitation

    def list_household_invitations(self, household_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, display_name, email, role, expires_at, created_at
                FROM household_invitations
                WHERE household_id = ? AND accepted_at IS NULL
                  AND revoked_at IS NULL AND expires_at > ?
                ORDER BY created_at DESC
                """,
                (household_id, now_iso()),
            ).fetchall()
        return [dict(row) for row in rows]

    def revoke_household_invitation(self, household_id: str, invitation_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE household_invitations SET revoked_at = ?
                WHERE id = ? AND household_id = ?
                  AND accepted_at IS NULL AND revoked_at IS NULL
                """,
                (now_iso(), invitation_id, household_id),
            )
        return cursor.rowcount > 0

    def accept_household_invitation(
        self, token: str, *, password_hash: str
    ) -> dict[str, Any] | None:
        token_hash = self._session_token_hash(token)
        timestamp = now_iso()
        with self.connect() as conn:
            invitation = conn.execute(
                """
                SELECT i.*, h.name AS household_name
                FROM household_invitations i
                JOIN households h ON h.id = i.household_id
                WHERE i.token_hash = ?
                LIMIT 1
                """,
                (token_hash,),
            ).fetchone()
            if (
                not invitation
                or invitation["accepted_at"]
                or invitation["revoked_at"]
                or datetime.fromisoformat(str(invitation["expires_at"])) <= datetime.now(UTC)
            ):
                return None
            if conn.execute(
                "SELECT 1 FROM users WHERE lower(email) = lower(?)",
                (invitation["email"],),
            ).fetchone():
                return None
            user_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO users(
                    id, display_name, email, password_hash, active,
                    owner_setup_complete, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 1, 1, ?, ?)
                """,
                (
                    user_id,
                    invitation["display_name"],
                    invitation["email"],
                    password_hash,
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                """
                INSERT INTO household_memberships(
                    id, household_id, user_id, role, active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    invitation["household_id"],
                    user_id,
                    invitation["role"],
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                "UPDATE household_invitations SET accepted_at = ? WHERE id = ?",
                (timestamp, invitation["id"]),
            )
        return {
            "user_id": user_id,
            "display_name": str(invitation["display_name"]),
            "email": str(invitation["email"]),
            "password_hash": password_hash,
            "owner_setup_complete": 1,
            "household_id": str(invitation["household_id"]),
            "household_name": str(invitation["household_name"]),
            "role": str(invitation["role"]),
        }

    def update_household_member(
        self,
        *,
        household_id: str,
        user_id: str,
        role: str,
        active: bool,
    ) -> dict[str, Any] | None:
        timestamp = now_iso()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT u.id, m.role FROM users u
                JOIN household_memberships m ON m.user_id = u.id
                WHERE u.id = ? AND m.household_id = ?
                """,
                (user_id, household_id),
            ).fetchone()
            if not row or row["role"] == "owner":
                return None
            conn.execute(
                "UPDATE users SET active = ?, updated_at = ? WHERE id = ?",
                (int(active), timestamp, user_id),
            )
            conn.execute(
                """
                UPDATE household_memberships
                SET role = ?, active = ?, updated_at = ?
                WHERE household_id = ? AND user_id = ?
                """,
                (role, int(active), timestamp, household_id, user_id),
            )
            if not active:
                conn.execute(
                    """
                    UPDATE auth_sessions SET revoked_at = ?
                    WHERE user_id = ? AND revoked_at IS NULL
                    """,
                    (timestamp, user_id),
                )
                conn.execute(
                    """
                    UPDATE api_tokens SET revoked_at = ?
                    WHERE user_id = ? AND revoked_at IS NULL
                    """,
                    (timestamp, user_id),
                )
        members = self.list_household_members(household_id)
        return next((member for member in members if member["id"] == user_id), None)

    def get_totp_credential(self, user_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, secret_encrypted, enabled, last_used_step,
                       created_at, updated_at
                FROM totp_credentials WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def put_pending_totp(self, user_id: str, secret_encrypted: str) -> None:
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO totp_credentials(
                    user_id, secret_encrypted, enabled, last_used_step,
                    created_at, updated_at
                ) VALUES (?, ?, 0, NULL, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    secret_encrypted = excluded.secret_encrypted,
                    enabled = 0,
                    last_used_step = NULL,
                    updated_at = excluded.updated_at
                """,
                (user_id, secret_encrypted, timestamp, timestamp),
            )

    def enable_totp(self, user_id: str, used_step: int) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE totp_credentials
                SET enabled = 1, last_used_step = ?, updated_at = ?
                WHERE user_id = ? AND enabled = 0
                """,
                (used_step, now_iso(), user_id),
            )
        return cursor.rowcount > 0

    def record_totp_step(self, user_id: str, used_step: int) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE totp_credentials
                SET last_used_step = ?, updated_at = ?
                WHERE user_id = ? AND enabled = 1
                  AND (last_used_step IS NULL OR last_used_step < ?)
                """,
                (used_step, now_iso(), user_id, used_step),
            )
        return cursor.rowcount > 0

    def delete_totp(self, user_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                "DELETE FROM totp_credentials WHERE user_id = ?",
                (user_id,),
            )
        return cursor.rowcount > 0

    def replace_recovery_codes(self, user_id: str, code_hashes: list[str]) -> None:
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute("DELETE FROM recovery_codes WHERE user_id = ?", (user_id,))
            conn.executemany(
                """
                INSERT INTO recovery_codes(id, user_id, code_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (str(uuid.uuid4()), user_id, code_hash, timestamp)
                    for code_hash in code_hashes
                ],
            )

    def recovery_code_count(self, user_id: str) -> int:
        with self.connect() as conn:
            return int(
                conn.execute(
                    "SELECT COUNT(*) FROM recovery_codes WHERE user_id = ? AND used_at IS NULL",
                    (user_id,),
                ).fetchone()[0]
            )

    def consume_recovery_code(self, user_id: str, code_hash: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                UPDATE recovery_codes SET used_at = ?
                WHERE user_id = ? AND code_hash = ? AND used_at IS NULL
                """,
                (now_iso(), user_id, code_hash),
            )
        return cursor.rowcount > 0

    def list_webauthn_credentials(self, user_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, credential_id, sign_count, device_type, backed_up,
                       transports_json, name, created_at, last_used_at
                FROM webauthn_credentials
                WHERE user_id = ? ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_webauthn_challenge(
        self,
        *,
        challenge: bytes,
        ceremony: str,
        purpose: str,
        rp_id: str,
        origin: str,
        user_id: str | None = None,
        session_id: str | None = None,
        expires_seconds: int = 300,
    ) -> str:
        challenge_id = str(uuid.uuid4())
        timestamp = now_iso()
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=expires_seconds)
        ).isoformat(timespec="microseconds")
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM webauthn_challenges WHERE expires_at <= ? OR used_at IS NOT NULL",
                (timestamp,),
            )
            conn.execute(
                """
                INSERT INTO webauthn_challenges(
                    id, challenge, user_id, session_id, ceremony, purpose,
                    rp_id, origin, expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    challenge_id,
                    challenge,
                    user_id,
                    session_id,
                    ceremony,
                    purpose,
                    rp_id,
                    origin,
                    expires_at,
                    timestamp,
                ),
            )
        return challenge_id

    def consume_webauthn_challenge(
        self,
        challenge_id: str,
        *,
        ceremony: str,
        purpose: str,
        session_id: str | None = None,
    ) -> dict[str, Any] | None:
        timestamp = now_iso()
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM webauthn_challenges
                WHERE id = ? AND ceremony = ? AND purpose = ?
                  AND used_at IS NULL AND expires_at > ?
                LIMIT 1
                """,
                (challenge_id, ceremony, purpose, timestamp),
            ).fetchone()
            if not row or (session_id is not None and row["session_id"] != session_id):
                return None
            conn.execute(
                "UPDATE webauthn_challenges SET used_at = ? WHERE id = ? AND used_at IS NULL",
                (timestamp, challenge_id),
            )
        return dict(row)

    def add_webauthn_credential(
        self,
        *,
        user_id: str,
        credential_id: bytes,
        public_key: bytes,
        sign_count: int,
        device_type: str,
        backed_up: bool,
        transports: list[str],
        name: str,
    ) -> dict[str, Any]:
        credential_row_id = str(uuid.uuid4())
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO webauthn_credentials(
                    id, user_id, credential_id, public_key, sign_count,
                    device_type, backed_up, transports_json, name, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    credential_row_id,
                    user_id,
                    credential_id,
                    public_key,
                    sign_count,
                    device_type,
                    int(backed_up),
                    json.dumps(transports),
                    " ".join(name.strip().split())[:100] or "Passkey",
                    timestamp,
                ),
            )
        return next(
            row for row in self.list_webauthn_credentials(user_id)
            if row["id"] == credential_row_id
        )

    def get_webauthn_credential(self, credential_id: bytes) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT c.*, u.display_name, u.email, u.password_hash,
                       u.owner_setup_complete, h.id AS household_id,
                       h.name AS household_name, m.role
                FROM webauthn_credentials c
                JOIN users u ON u.id = c.user_id
                JOIN household_memberships m ON m.user_id = u.id
                JOIN households h ON h.id = m.household_id
                WHERE c.credential_id = ? AND u.active = 1 AND m.active = 1
                LIMIT 1
                """,
                (credential_id,),
            ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["user_id"] = result.pop("user_id")
        return result

    def update_webauthn_credential(
        self, credential_row_id: str, sign_count: int, device_type: str, backed_up: bool
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE webauthn_credentials
                SET sign_count = ?, device_type = ?, backed_up = ?, last_used_at = ?
                WHERE id = ?
                """,
                (sign_count, device_type, int(backed_up), now_iso(), credential_row_id),
            )

    def delete_webauthn_credential(self, user_id: str, credential_row_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                "DELETE FROM webauthn_credentials WHERE id = ? AND user_id = ?",
                (credential_row_id, user_id),
            )
        return cursor.rowcount > 0

    def ping(self) -> bool:
        try:
            with self.connect() as conn:
                return conn.execute("SELECT 1").fetchone()[0] == 1
        except sqlite3.Error:
            return False

    def auth_failure_count(self, source_hash: str, window_seconds: int) -> int:
        cutoff = (datetime.now(UTC) - timedelta(seconds=window_seconds)).isoformat(
            timespec="seconds"
        )
        with self.connect() as conn:
            conn.execute("DELETE FROM auth_attempts WHERE failed_at < ?", (cutoff,))
            return int(
                conn.execute(
                    "SELECT COUNT(*) FROM auth_attempts WHERE source_hash = ? AND failed_at >= ?",
                    (source_hash, cutoff),
                ).fetchone()[0]
            )

    def record_auth_failure(self, source_hash: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO auth_attempts(source_hash, failed_at) VALUES (?, ?)",
                (source_hash, now_iso()),
            )

    def clear_auth_failures(self, source_hash: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM auth_attempts WHERE source_hash = ?",
                (source_hash,),
            )

    def add_audit_event(
        self,
        *,
        category: str,
        action: str,
        outcome: str,
        source_hash: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        event_id = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events(
                    id, category, action, outcome, source_hash, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    category[:80],
                    action[:300],
                    outcome[:40],
                    source_hash,
                    json.dumps(details or {}, ensure_ascii=False, separators=(",", ":")),
                    now_iso(),
                ),
            )
        return event_id

    def list_audit_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, category, action, outcome, source_hash, details_json, created_at
                FROM audit_events
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (max(1, min(limit, 500)),),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            event = dict(row)
            try:
                event["details"] = json.loads(event.pop("details_json"))
            except (json.JSONDecodeError, TypeError):
                event["details"] = {}
                event.pop("details_json", None)
            events.append(event)
        return events

    def catalog_summary(self) -> dict[str, int]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM catalog_products WHERE active = 1) AS products,
                    (SELECT COUNT(*) FROM catalog_product_variants) AS variants,
                    (SELECT COUNT(*) FROM catalog_barcodes) AS barcodes,
                    (SELECT COUNT(*) FROM stock_lots WHERE quantity > 0) AS stock_lots
                """
            ).fetchone()
        return {key: int(row[key] or 0) for key in row.keys()} if row else {}

    def catalog_master_data(self) -> dict[str, list[dict[str, Any]]]:
        with self.connect() as conn:
            locations = conn.execute(
                """
                SELECT l.*,
                    (SELECT COUNT(*) FROM catalog_products p
                     WHERE p.default_location_id = l.id AND p.active = 1) AS usage_count
                FROM catalog_locations l
                WHERE l.active = 1
                ORDER BY l.name COLLATE NOCASE
                """
            ).fetchall()
            units = conn.execute(
                """
                SELECT u.*,
                    (SELECT COUNT(*) FROM catalog_products p
                     WHERE p.default_quantity_unit_id = u.id AND p.active = 1) AS usage_count
                FROM catalog_quantity_units u
                WHERE u.active = 1
                ORDER BY u.name COLLATE NOCASE
                """
            ).fetchall()
            groups = conn.execute(
                """
                SELECT g.*,
                    (SELECT COUNT(*) FROM catalog_products p
                     WHERE p.product_group_id = g.id AND p.active = 1) AS usage_count
                FROM catalog_product_groups g
                WHERE g.active = 1
                ORDER BY g.name COLLATE NOCASE
                """
            ).fetchall()
        return {
            "locations": [dict(row) for row in locations],
            "quantity_units": [dict(row) for row in units],
            "product_groups": [dict(row) for row in groups],
        }

    def list_catalog_products(self, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
        needle = f"%{normalize_key(query)}%"
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.*,
                    g.name AS product_group_name,
                    l.name AS default_location_name,
                    u.name AS default_quantity_unit_name,
                    (SELECT COUNT(*) FROM catalog_product_variants v WHERE v.product_id = p.id) AS variant_count,
                    (SELECT COUNT(*) FROM catalog_barcodes b
                        JOIN catalog_product_variants v ON v.id = b.variant_id
                        WHERE v.product_id = p.id) AS barcode_count,
                    COALESCE((SELECT SUM(s.quantity) FROM stock_lots s WHERE s.product_id = p.id), 0) AS stock_quantity,
                    (SELECT CAST(r.external_id AS INTEGER) FROM catalog_external_refs r
                        WHERE r.product_id = p.id AND r.source = 'grocy' LIMIT 1) AS grocy_product_id
                FROM catalog_products p
                LEFT JOIN catalog_product_groups g ON g.id = p.product_group_id
                LEFT JOIN catalog_locations l ON l.id = p.default_location_id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                WHERE p.active = 1 AND (? = '%%' OR p.normalized_name LIKE ?)
                ORDER BY p.name COLLATE NOCASE
                LIMIT ?
                """,
                (needle, needle, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_catalog_product(self, product_id: str) -> dict[str, Any] | None:
        products = self.list_catalog_products(limit=10000)
        return next((product for product in products if product["id"] == product_id), None)

    def get_catalog_product_detail(self, product_id: str) -> dict[str, Any] | None:
        product = self.get_catalog_product(product_id)
        if not product:
            return None
        with self.connect() as conn:
            row = conn.execute(
                "SELECT notes, active, created_at, updated_at FROM catalog_products WHERE id = ?",
                (product_id,),
            ).fetchone()
            variants = conn.execute(
                """
                SELECT v.*,
                    (SELECT COUNT(*) FROM receipt_items i WHERE i.catalog_variant_id = v.id) AS receipt_count,
                    (SELECT COUNT(*) FROM stock_lots s WHERE s.variant_id = v.id) AS stock_lot_count
                FROM catalog_product_variants v
                WHERE v.product_id = ?
                ORDER BY COALESCE(v.brand, ''), COALESCE(v.name, ''), v.created_at
                """,
                (product_id,),
            ).fetchall()
            result_variants: list[dict[str, Any]] = []
            for variant in variants:
                entry = dict(variant)
                barcodes = conn.execute(
                    """
                    SELECT barcode, symbology, is_primary, created_at, updated_at
                    FROM catalog_barcodes WHERE variant_id = ?
                    ORDER BY is_primary DESC, barcode
                    """,
                    (variant["id"],),
                ).fetchall()
                entry["barcodes"] = [dict(barcode) for barcode in barcodes]
                result_variants.append(entry)
        return {
            **product,
            **(dict(row) if row else {}),
            "variants": result_variants,
        }

    @staticmethod
    def _require_active_master(
        conn: sqlite3.Connection, table: str, row_id: int | None, label: str
    ) -> None:
        if row_id is None:
            return
        row = conn.execute(
            # The caller supplies only fixed catalog table names; values stay bound.
            f"SELECT id FROM {table} WHERE id = ? AND active = 1",  # nosec B608
            (row_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"{label} wurde nicht gefunden oder ist archiviert")

    @staticmethod
    def _validate_reorder_rule(
        minimum_stock_quantity: float, shopping_target_quantity: float
    ) -> None:
        minimum = float(minimum_stock_quantity)
        target = float(shopping_target_quantity)
        if minimum < 0 or target < 0:
            raise ValueError("Mindestbestand und Auffüllziel dürfen nicht negativ sein")
        if target > 0 and target <= minimum:
            raise ValueError("Das Auffüllziel muss größer als der Mindestbestand sein")

    def update_catalog_product(
        self,
        product_id: str,
        *,
        name: str,
        product_group_id: int | None,
        default_location_id: int | None,
        default_quantity_unit_id: int | None,
        default_best_before_days: int,
        minimum_stock_quantity: float,
        shopping_target_quantity: float,
        image_url: str | None,
        notes: str,
        expected_updated_at: str,
    ) -> dict[str, Any]:
        self._validate_reorder_rule(
            minimum_stock_quantity, shopping_target_quantity
        )
        clean_name = name.strip()
        normalized_name = normalize_key(clean_name)
        if not normalized_name:
            raise ValueError("Der Produktname darf nicht leer sein")
        with self.connect() as conn:
            current = conn.execute(
                "SELECT * FROM catalog_products WHERE id = ? AND active = 1", (product_id,)
            ).fetchone()
            if not current:
                raise KeyError("Produkt nicht gefunden")
            if str(current["updated_at"]) != expected_updated_at:
                raise RuntimeError("Das Produkt wurde inzwischen geändert. Bitte neu laden.")
            duplicate = conn.execute(
                "SELECT id FROM catalog_products WHERE normalized_name = ? AND id <> ?",
                (normalized_name, product_id),
            ).fetchone()
            if duplicate:
                raise ValueError("Ein anderes Produkt verwendet bereits diesen Namen")
            self._require_active_master(
                conn, "catalog_product_groups", product_group_id, "Produktgruppe"
            )
            self._require_active_master(
                conn, "catalog_locations", default_location_id, "Lagerort"
            )
            self._require_active_master(
                conn, "catalog_quantity_units", default_quantity_unit_id, "Einheit"
            )
            timestamp = now_iso()
            if normalize_key(str(current["name"])) != normalized_name:
                conn.execute(
                    """
                    INSERT INTO catalog_aliases(alias_key, product_id, source, created_at, updated_at)
                    VALUES (?, ?, 'product_rename', ?, ?)
                    ON CONFLICT(alias_key, product_id) DO UPDATE SET updated_at = excluded.updated_at
                    """,
                    (normalize_key(str(current["name"])), product_id, timestamp, timestamp),
                )
            conn.execute(
                """
                UPDATE catalog_products
                SET name = ?, normalized_name = ?, product_group_id = ?,
                    default_location_id = ?, default_quantity_unit_id = ?,
                    default_best_before_days = ?, minimum_stock_quantity = ?,
                    shopping_target_quantity = ?, image_url = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    clean_name,
                    normalized_name,
                    product_group_id,
                    default_location_id,
                    default_quantity_unit_id,
                    default_best_before_days,
                    round(float(minimum_stock_quantity), 6),
                    round(float(shopping_target_quantity), 6),
                    image_url,
                    notes.strip(),
                    timestamp,
                    product_id,
                ),
            )
        updated = self.get_catalog_product_detail(product_id)
        if not updated:
            raise RuntimeError("Das Produkt konnte nicht geladen werden")
        return updated

    def create_catalog_variant(
        self,
        product_id: str,
        *,
        name: str | None,
        brand: str | None,
        package_amount: float | None,
        package_unit: str | None,
        image_url: str | None,
    ) -> dict[str, Any]:
        variant_id = str(uuid.uuid4())
        timestamp = now_iso()
        with self.connect() as conn:
            if not conn.execute(
                "SELECT id FROM catalog_products WHERE id = ? AND active = 1", (product_id,)
            ).fetchone():
                raise KeyError("Produkt nicht gefunden")
            conn.execute(
                """
                INSERT INTO catalog_product_variants(
                    id, product_id, name, brand, package_amount, package_unit,
                    image_url, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    variant_id,
                    product_id,
                    (name or "").strip() or None,
                    (brand or "").strip() or None,
                    package_amount,
                    (package_unit or "").strip() or None,
                    image_url,
                    timestamp,
                    timestamp,
                ),
            )
        result = self.get_catalog_product_detail(product_id)
        if not result:
            raise RuntimeError("Die Variante konnte nicht geladen werden")
        return result

    def update_catalog_variant(
        self,
        variant_id: str,
        *,
        name: str | None,
        brand: str | None,
        package_amount: float | None,
        package_unit: str | None,
        image_url: str | None,
        expected_updated_at: str,
    ) -> dict[str, Any]:
        with self.connect() as conn:
            current = conn.execute(
                "SELECT * FROM catalog_product_variants WHERE id = ?", (variant_id,)
            ).fetchone()
            if not current:
                raise KeyError("Variante nicht gefunden")
            if str(current["updated_at"]) != expected_updated_at:
                raise RuntimeError("Die Variante wurde inzwischen geändert. Bitte neu laden.")
            timestamp = now_iso()
            conn.execute(
                """
                UPDATE catalog_product_variants
                SET name = ?, brand = ?, package_amount = ?, package_unit = ?,
                    image_url = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    (name or "").strip() or None,
                    (brand or "").strip() or None,
                    package_amount,
                    (package_unit or "").strip() or None,
                    image_url,
                    timestamp,
                    variant_id,
                ),
            )
            product_id = str(current["product_id"])
        result = self.get_catalog_product_detail(product_id)
        if not result:
            raise RuntimeError("Das Produkt konnte nicht geladen werden")
        return result

    def delete_catalog_variant(self, variant_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            current = conn.execute(
                "SELECT product_id FROM catalog_product_variants WHERE id = ?", (variant_id,)
            ).fetchone()
            if not current:
                raise KeyError("Variante nicht gefunden")
            references = int(conn.execute(
                "SELECT COUNT(*) FROM receipt_items WHERE catalog_variant_id = ?", (variant_id,)
            ).fetchone()[0]) + int(conn.execute(
                "SELECT COUNT(*) FROM stock_lots WHERE variant_id = ?", (variant_id,)
            ).fetchone()[0]) + int(conn.execute(
                "SELECT COUNT(*) FROM scan_drafts WHERE variant_id = ?", (variant_id,)
            ).fetchone()[0])
            if references:
                raise ValueError(
                    f"Die Variante wird noch {references}-mal verwendet und kann nicht gelöscht werden"
                )
            product_id = str(current["product_id"])
            conn.execute("DELETE FROM catalog_product_variants WHERE id = ?", (variant_id,))
        result = self.get_catalog_product_detail(product_id)
        if not result:
            raise RuntimeError("Das Produkt konnte nicht geladen werden")
        return result

    def add_catalog_barcode(
        self, variant_id: str, *, barcode: str, symbology: str
    ) -> dict[str, Any]:
        timestamp = now_iso()
        with self.connect() as conn:
            variant = conn.execute(
                "SELECT product_id FROM catalog_product_variants WHERE id = ?", (variant_id,)
            ).fetchone()
            if not variant:
                raise KeyError("Variante nicht gefunden")
            existing = conn.execute(
                "SELECT variant_id FROM catalog_barcodes WHERE barcode = ?", (barcode,)
            ).fetchone()
            if existing and str(existing["variant_id"]) != variant_id:
                raise ValueError("Dieser Barcode gehört bereits zu einer anderen Variante")
            conn.execute(
                """
                INSERT INTO catalog_barcodes(
                    barcode, variant_id, symbology, is_primary, created_at, updated_at
                ) VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(barcode) DO UPDATE SET
                    symbology = excluded.symbology, updated_at = excluded.updated_at
                """,
                (barcode, variant_id, symbology, timestamp, timestamp),
            )
            product_id = str(variant["product_id"])
        result = self.get_catalog_product_detail(product_id)
        if not result:
            raise RuntimeError("Das Produkt konnte nicht geladen werden")
        return result

    def delete_catalog_barcode(self, variant_id: str, barcode: str) -> dict[str, Any]:
        with self.connect() as conn:
            variant = conn.execute(
                "SELECT product_id FROM catalog_product_variants WHERE id = ?", (variant_id,)
            ).fetchone()
            if not variant:
                raise KeyError("Variante nicht gefunden")
            deleted = conn.execute(
                "DELETE FROM catalog_barcodes WHERE barcode = ? AND variant_id = ?",
                (barcode, variant_id),
            ).rowcount
            if not deleted:
                raise KeyError("Barcode nicht gefunden")
            product_id = str(variant["product_id"])
        result = self.get_catalog_product_detail(product_id)
        if not result:
            raise RuntimeError("Das Produkt konnte nicht geladen werden")
        return result

    @staticmethod
    def _master_definition(kind: str) -> tuple[str, str]:
        definitions = {
            "locations": ("catalog_locations", "default_location_id"),
            "quantity-units": ("catalog_quantity_units", "default_quantity_unit_id"),
            "product-groups": ("catalog_product_groups", "product_group_id"),
        }
        if kind not in definitions:
            raise KeyError("Unbekannter Stammdatentyp")
        return definitions[kind]

    def create_catalog_master_data(
        self,
        kind: str,
        *,
        name: str,
        description: str,
        is_freezer: bool,
        name_plural: str | None,
    ) -> dict[str, Any]:
        table, _ = self._master_definition(kind)
        timestamp = now_iso()
        columns = "name, description, active, created_at, updated_at"
        values: list[Any] = [name.strip(), description.strip(), 1, timestamp, timestamp]
        if kind == "locations":
            columns += ", is_freezer"
            values.append(int(is_freezer))
        elif kind == "quantity-units":
            columns += ", name_plural"
            values.append((name_plural or name).strip())
        try:
            with self.connect() as conn:
                placeholders = ", ".join("?" for _ in values)
                cursor = conn.execute(
                    # Table/columns come from _master_definition and fixed branches.
                    f"INSERT INTO {table}({columns}) VALUES ({placeholders})",  # nosec B608
                    values,
                )
                row_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError("Dieser Name ist bereits vorhanden") from exc
        return self._get_master_data_item(kind, row_id)

    def _get_master_data_item(self, kind: str, row_id: int) -> dict[str, Any]:
        self._master_definition(kind)
        queries = {
            "locations": """
                SELECT m.*,
                    (SELECT COUNT(*) FROM catalog_products p
                     WHERE p.default_location_id = m.id AND p.active = 1) AS usage_count
                FROM catalog_locations m WHERE m.id = ?
            """,
            "quantity-units": """
                SELECT m.*,
                    (SELECT COUNT(*) FROM catalog_products p
                     WHERE p.default_quantity_unit_id = m.id AND p.active = 1) AS usage_count
                FROM catalog_quantity_units m WHERE m.id = ?
            """,
            "product-groups": """
                SELECT m.*,
                    (SELECT COUNT(*) FROM catalog_products p
                     WHERE p.product_group_id = m.id AND p.active = 1) AS usage_count
                FROM catalog_product_groups m WHERE m.id = ?
            """,
        }
        with self.connect() as conn:
            row = conn.execute(queries[kind], (row_id,)).fetchone()
        if not row:
            raise KeyError("Stammdatensatz nicht gefunden")
        return dict(row)

    def update_catalog_master_data(
        self,
        kind: str,
        row_id: int,
        *,
        name: str,
        description: str,
        is_freezer: bool,
        name_plural: str | None,
        expected_updated_at: str,
    ) -> dict[str, Any]:
        table, _ = self._master_definition(kind)
        with self.connect() as conn:
            current = conn.execute(
                f"SELECT * FROM {table} WHERE id = ? AND active = 1",  # nosec B608
                (row_id,),
            ).fetchone()
            if not current:
                raise KeyError("Stammdatensatz nicht gefunden")
            if str(current["updated_at"]) != expected_updated_at:
                raise RuntimeError("Der Eintrag wurde inzwischen geändert. Bitte neu laden.")
            timestamp = now_iso()
            assignments = "name = ?, description = ?, updated_at = ?"
            values: list[Any] = [name.strip(), description.strip(), timestamp]
            if kind == "locations":
                assignments += ", is_freezer = ?"
                values.append(int(is_freezer))
            elif kind == "quantity-units":
                assignments += ", name_plural = ?"
                values.append((name_plural or name).strip())
            values.append(row_id)
            try:
                conn.execute(
                    # Both identifiers are selected from fixed master-data branches.
                    f"UPDATE {table} SET {assignments} WHERE id = ?",  # nosec B608
                    values,
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("Dieser Name ist bereits vorhanden") from exc
        return self._get_master_data_item(kind, row_id)

    def archive_catalog_master_data(self, kind: str, row_id: int) -> dict[str, Any]:
        table, reference_column = self._master_definition(kind)
        with self.connect() as conn:
            current = conn.execute(
                f"SELECT * FROM {table} WHERE id = ? AND active = 1",  # nosec B608
                (row_id,),
            ).fetchone()
            if not current:
                raise KeyError("Stammdatensatz nicht gefunden")
            usage_count = int(conn.execute(
                f"SELECT COUNT(*) FROM catalog_products WHERE {reference_column} = ? AND active = 1",  # nosec B608
                (row_id,),
            ).fetchone()[0])
            if usage_count:
                raise ValueError(
                    f"Der Eintrag wird noch von {usage_count} Produkten verwendet. Bitte zuerst neu zuordnen."
                )
            conn.execute(
                f"UPDATE {table} SET active = 0, updated_at = ? WHERE id = ?",  # nosec B608
                (now_iso(), row_id),
            )
        return self._get_master_data_item(kind, row_id)

    def catalog_price_history(
        self, product_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT i.id AS receipt_item_id, i.receipt_id, r.purchase_date,
                    r.store_name, r.retailer, r.currency, i.quantity,
                    COALESCE(i.unit_price,
                        CASE WHEN i.quantity > 0 THEN i.total_price / i.quantity END
                    ) AS unit_price,
                    i.total_price, i.barcode, i.catalog_variant_id,
                    v.name AS variant_name, v.brand,
                    v.package_amount, v.package_unit
                FROM receipt_items i
                JOIN receipts r ON r.id = i.receipt_id
                LEFT JOIN catalog_product_variants v ON v.id = i.catalog_variant_id
                WHERE i.catalog_product_id = ? AND i.imported = 1
                ORDER BY r.purchase_date DESC, r.created_at DESC, i.position
                LIMIT ?
                """,
                (product_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def price_insights(self, limit: int = 100) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT p.id AS product_id, p.name AS product_name, p.image_url,
                    q.name AS quantity_unit_name, i.id AS receipt_item_id,
                    i.receipt_id, r.purchase_date, r.created_at AS receipt_created_at,
                    r.store_name, r.retailer, r.currency, i.quantity,
                    COALESCE(i.unit_price,
                        CASE WHEN i.quantity > 0 THEN i.total_price / i.quantity END
                    ) AS unit_price,
                    i.catalog_variant_id, v.name AS variant_name, v.brand,
                    v.package_amount, v.package_unit
                FROM receipt_items i
                JOIN receipts r ON r.id = i.receipt_id
                JOIN catalog_products p ON p.id = i.catalog_product_id
                LEFT JOIN catalog_quantity_units q ON q.id = p.default_quantity_unit_id
                LEFT JOIN catalog_product_variants v ON v.id = i.catalog_variant_id
                WHERE i.imported = 1 AND p.active = 1
                    AND COALESCE(i.unit_price,
                        CASE WHEN i.quantity > 0 THEN i.total_price / i.quantity END
                    ) > 0
                ORDER BY COALESCE(r.purchase_date, substr(r.created_at, 1, 10)) DESC,
                    r.created_at DESC, i.position
                """
            ).fetchall()

        products: dict[str, dict[str, Any]] = {}
        for source in rows:
            row = dict(source)
            product_id = str(row["product_id"])
            product = products.setdefault(
                product_id,
                {
                    "product_id": product_id,
                    "product_name": row["product_name"],
                    "image_url": row["image_url"],
                    "quantity_unit_name": row["quantity_unit_name"],
                    "observations": [],
                    "stores": {},
                },
            )
            price = round(float(row["unit_price"]), 4)
            store_label = str(row["retailer"] or row["store_name"] or "Unbekanntes Geschäft").strip()
            store_key = retailer_key(store_label)
            observed_at = row["purchase_date"] or str(row["receipt_created_at"] or "")[:10] or None
            observation = {
                "price": price,
                "date": observed_at,
                "store_key": store_key,
                "store_name": store_label,
                "currency": row["currency"],
            }
            product["observations"].append(observation)
            store = product["stores"].setdefault(
                store_key,
                {
                    "store_key": store_key,
                    "store_name": store_label,
                    "prices": [],
                    "latest_price": price,
                    "latest_date": observed_at,
                },
            )
            store["prices"].append(price)

        summaries: list[dict[str, Any]] = []
        global_stores: set[str] = set()
        observation_count = 0
        for product in products.values():
            observations = product.pop("observations")
            prices = [item["price"] for item in observations]
            latest = observations[0]
            previous_price = observations[1]["price"] if len(observations) > 1 else None
            change_amount = round(latest["price"] - previous_price, 4) if previous_price else None
            change_percent = (
                round(change_amount / previous_price * 100, 2)
                if change_amount is not None and previous_price > 0
                else None
            )
            stores = []
            for store in product.pop("stores").values():
                store_prices = store.pop("prices")
                store["lowest_price"] = round(min(store_prices), 4)
                store["average_price"] = round(sum(store_prices) / len(store_prices), 4)
                store["observation_count"] = len(store_prices)
                stores.append(store)
                global_stores.add(store["store_key"])
            stores.sort(key=lambda item: (item["latest_price"], item["store_name"].casefold()))
            observation_count += len(observations)
            summaries.append(
                {
                    **product,
                    "currency": latest["currency"],
                    "observation_count": len(observations),
                    "store_count": len(stores),
                    "latest_price": latest["price"],
                    "latest_date": latest["date"],
                    "latest_store": latest["store_name"],
                    "previous_price": previous_price,
                    "lowest_price": round(min(prices), 4),
                    "highest_price": round(max(prices), 4),
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                    "stores": stores,
                }
            )

        summaries.sort(key=lambda item: (item["latest_date"] or "", item["product_name"].casefold()), reverse=True)
        selected = summaries[:limit]
        return {
            "products": selected,
            "product_count": len(summaries),
            "store_count": len(global_stores),
            "observation_count": observation_count,
            "generated_at": now_iso(),
        }

    def budget_settings(self, household_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT monthly_limit_cents, currency, warning_percent, updated_at
                FROM household_budget_settings WHERE household_id = ?
                """,
                (household_id,),
            ).fetchone()
        if not row:
            return {
                "configured": False,
                "monthly_limit": None,
                "currency": "EUR",
                "warning_percent": 80,
                "updated_at": None,
            }
        return {
            "configured": True,
            "monthly_limit": round(int(row["monthly_limit_cents"]) / 100, 2),
            "currency": str(row["currency"]),
            "warning_percent": int(row["warning_percent"]),
            "updated_at": str(row["updated_at"]),
        }

    def set_budget_settings(
        self,
        *,
        household_id: str,
        user_id: str,
        monthly_limit: float | None,
        warning_percent: int = 80,
    ) -> dict[str, Any]:
        with self.connect() as conn:
            if monthly_limit is None:
                conn.execute(
                    "DELETE FROM household_budget_settings WHERE household_id = ?",
                    (household_id,),
                )
            else:
                limit_cents = int(round(float(monthly_limit) * 100))
                if limit_cents <= 0 or limit_cents > 100_000_000:
                    raise ValueError("Das Monatsbudget muss zwischen 1 und 1.000.000 Euro liegen")
                if warning_percent < 50 or warning_percent > 100:
                    raise ValueError("Die Vorwarnung muss zwischen 50 und 100 Prozent liegen")
                timestamp = now_iso()
                conn.execute(
                    """
                    INSERT INTO household_budget_settings(
                        household_id, monthly_limit_cents, currency,
                        warning_percent, updated_by_user_id, created_at, updated_at
                    ) VALUES (?, ?, 'EUR', ?, ?, ?, ?)
                    ON CONFLICT(household_id) DO UPDATE SET
                        monthly_limit_cents = excluded.monthly_limit_cents,
                        warning_percent = excluded.warning_percent,
                        updated_by_user_id = excluded.updated_by_user_id,
                        updated_at = excluded.updated_at
                    """,
                    (
                        household_id,
                        limit_cents,
                        warning_percent,
                        user_id,
                        timestamp,
                        timestamp,
                    ),
                )
        return self.budget_settings(household_id)

    def budget_overview(
        self,
        household_id: str,
        months: int = 6,
        *,
        today: date | None = None,
    ) -> dict[str, Any]:
        current_day = today or datetime.now(UTC).date()
        history_months = max(1, min(int(months), 24))
        current_month = current_day.replace(day=1)
        previous_month = _shift_month(current_month, -1)
        previous_cutoff = previous_month.replace(
            day=min(current_day.day, calendar.monthrange(previous_month.year, previous_month.month)[1])
        )
        history_start = _shift_month(current_month, -(history_months - 1))
        query_start = min(history_start, previous_month)
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT r.id, r.store_name, r.retailer, r.currency, r.total,
                       COALESCE(NULLIF(r.purchase_date, ''), substr(r.created_at, 1, 10)) AS budget_date
                FROM receipts r
                WHERE COALESCE(NULLIF(r.purchase_date, ''), substr(r.created_at, 1, 10)) >= ?
                  AND COALESCE(NULLIF(r.purchase_date, ''), substr(r.created_at, 1, 10)) <= ?
                  AND EXISTS(
                      SELECT 1 FROM receipt_items i
                      WHERE i.receipt_id = r.id AND i.imported = 1
                  )
                ORDER BY budget_date, r.created_at
                """,
                (query_start.isoformat(), current_day.isoformat()),
            ).fetchall()
            pending_receipt_count = int(
                conn.execute(
                    """
                    SELECT COUNT(*) FROM receipts r
                    WHERE COALESCE(NULLIF(r.purchase_date, ''), substr(r.created_at, 1, 10)) >= ?
                      AND COALESCE(NULLIF(r.purchase_date, ''), substr(r.created_at, 1, 10)) <= ?
                      AND COALESCE(r.total, 0) > 0
                      AND NOT EXISTS(
                          SELECT 1 FROM receipt_items i
                          WHERE i.receipt_id = r.id AND i.imported = 1
                      )
                    """,
                    (current_month.isoformat(), current_day.isoformat()),
                ).fetchone()[0]
            )

        settings = self.budget_settings(household_id)
        currency = str(settings["currency"])
        month_keys = [
            _shift_month(history_start, offset).strftime("%Y-%m")
            for offset in range(history_months)
        ]
        month_totals = {
            key: {"month": key, "spent": 0.0, "receipt_count": 0, "is_current": key == current_month.strftime("%Y-%m")}
            for key in month_keys
        }
        current_rows: list[dict[str, Any]] = []
        previous_spent = 0.0
        previous_receipt_count = 0
        for source in rows:
            row = dict(source)
            try:
                observed = date.fromisoformat(str(row["budget_date"])[:10])
            except ValueError:
                continue
            amount = float(row["total"] or 0)
            if str(row["currency"] or "EUR") != currency or amount <= 0:
                continue
            key = observed.strftime("%Y-%m")
            if key in month_totals:
                month_totals[key]["spent"] += amount
                month_totals[key]["receipt_count"] += 1
            if current_month <= observed <= current_day:
                current_rows.append(row)
            if previous_month <= observed <= previous_cutoff:
                previous_spent += amount
                previous_receipt_count += 1

        for summary in month_totals.values():
            summary["spent"] = round(float(summary["spent"]), 2)

        spent = round(sum(float(row["total"] or 0) for row in current_rows), 2)
        receipt_count = len(current_rows)
        days_total = calendar.monthrange(current_day.year, current_day.month)[1]
        days_elapsed = current_day.day
        days_remaining = max(days_total - days_elapsed, 0)
        forecast = round(spent / days_elapsed * days_total, 2) if days_elapsed else spent
        monthly_limit = settings["monthly_limit"]
        remaining = round(float(monthly_limit) - spent, 2) if monthly_limit is not None else None
        percent_used = (
            round(spent / float(monthly_limit) * 100, 2)
            if monthly_limit is not None and float(monthly_limit) > 0
            else None
        )
        if monthly_limit is None:
            status = "unconfigured"
        elif spent >= float(monthly_limit):
            status = "over"
        elif (
            (percent_used or 0) >= int(settings["warning_percent"])
            or forecast > float(monthly_limit)
        ):
            status = "watch"
        else:
            status = "on_track"

        store_groups: dict[str, dict[str, Any]] = {}
        for row in current_rows:
            label = str(row["retailer"] or row["store_name"] or "Unbekanntes Geschäft").strip()
            key = retailer_key(label)
            store = store_groups.setdefault(
                key,
                {"store_key": key, "store_name": label, "spent": 0.0, "receipt_count": 0},
            )
            store["spent"] += float(row["total"] or 0)
            store["receipt_count"] += 1
        stores = []
        for store in store_groups.values():
            store["spent"] = round(float(store["spent"]), 2)
            store["share_percent"] = round(store["spent"] / spent * 100, 2) if spent else 0.0
            stores.append(store)
        stores.sort(key=lambda item: (-item["spent"], item["store_name"].casefold()))

        comparison_amount = round(spent - previous_spent, 2)
        comparison_percent = (
            round(comparison_amount / previous_spent * 100, 2)
            if previous_spent > 0
            else None
        )
        confirmed_current = [
            dict(row)
            for row in rows
            if current_month.isoformat() <= str(row["budget_date"]) <= current_day.isoformat()
        ]
        missing_total_count = sum(1 for row in confirmed_current if float(row["total"] or 0) <= 0)
        other_currency_count = sum(
            1
            for row in confirmed_current
            if float(row["total"] or 0) > 0 and str(row["currency"] or "EUR") != currency
        )
        confirmed_receipt_count = len(confirmed_current)
        coverage_percent = (
            round(receipt_count / confirmed_receipt_count * 100, 2)
            if confirmed_receipt_count
            else 0.0
        )

        return {
            "settings": settings,
            "current_period": {
                "month": current_month.strftime("%Y-%m"),
                "start_date": current_month.isoformat(),
                "as_of_date": current_day.isoformat(),
                "spent": spent,
                "receipt_count": receipt_count,
                "average_receipt": round(spent / receipt_count, 2) if receipt_count else 0.0,
                "remaining": remaining,
                "percent_used": percent_used,
                "forecast": forecast,
                "days_elapsed": days_elapsed,
                "days_total": days_total,
                "days_remaining": days_remaining,
                "daily_available": (
                    round(remaining / max(days_remaining, 1), 2)
                    if remaining is not None
                    else None
                ),
                "status": status,
                "latest_purchase_date": max(
                    (str(row["budget_date"]) for row in current_rows), default=None
                ),
            },
            "comparison": {
                "start_date": previous_month.isoformat(),
                "end_date": previous_cutoff.isoformat(),
                "spent": round(previous_spent, 2),
                "receipt_count": previous_receipt_count,
                "change_amount": comparison_amount,
                "change_percent": comparison_percent,
            },
            "months": list(month_totals.values()),
            "stores": stores[:8],
            "data_quality": {
                "confirmed_receipt_count": confirmed_receipt_count,
                "counted_receipt_count": receipt_count,
                "pending_receipt_count": pending_receipt_count,
                "missing_total_count": missing_total_count,
                "other_currency_receipt_count": other_currency_count,
                "coverage_percent": coverage_percent,
            },
            "generated_at": now_iso(),
        }

    def catalog_product_by_barcode(self, barcode: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT p.*, v.id AS variant_id, v.name AS variant_name,
                    v.brand, v.package_amount, v.package_unit, b.barcode
                FROM catalog_barcodes b
                JOIN catalog_product_variants v ON v.id = b.variant_id
                JOIN catalog_products p ON p.id = v.product_id
                WHERE b.barcode = ?
                """,
                (barcode.strip(),),
            ).fetchone()
        return dict(row) if row else None

    def create_catalog_product(
        self,
        *,
        name: str,
        location_id: int | None = None,
        new_location_name: str | None = None,
        new_location_is_freezer: bool = False,
        quantity_unit_id: int | None = None,
        new_quantity_unit_name: str | None = None,
        product_group_id: int | None = None,
        new_product_group_name: str | None = None,
        default_best_before_days: int = 0,
        minimum_stock_quantity: float = 0,
        shopping_target_quantity: float = 0,
        brand: str | None = None,
        barcode: str | None = None,
    ) -> dict[str, Any]:
        self._validate_reorder_rule(
            minimum_stock_quantity, shopping_target_quantity
        )
        with self.connect() as conn:
            timestamp = now_iso()
            if new_location_name:
                conn.execute(
                    """
                    INSERT INTO catalog_locations(
                        name, is_freezer, created_at, updated_at
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        is_freezer = excluded.is_freezer,
                        updated_at = excluded.updated_at
                    """,
                    (new_location_name.strip(), int(new_location_is_freezer), timestamp, timestamp),
                )
                row = conn.execute(
                    "SELECT id FROM catalog_locations WHERE name = ? COLLATE NOCASE",
                    (new_location_name.strip(),),
                ).fetchone()
                location_id = int(row["id"])
            if new_quantity_unit_name:
                conn.execute(
                    """
                    INSERT INTO catalog_quantity_units(
                        name, name_plural, created_at, updated_at
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(name) DO NOTHING
                    """,
                    (
                        new_quantity_unit_name.strip(),
                        new_quantity_unit_name.strip(),
                        timestamp,
                        timestamp,
                    ),
                )
                row = conn.execute(
                    "SELECT id FROM catalog_quantity_units WHERE name = ? COLLATE NOCASE",
                    (new_quantity_unit_name.strip(),),
                ).fetchone()
                quantity_unit_id = int(row["id"])
            if new_product_group_name:
                conn.execute(
                    """
                    INSERT INTO catalog_product_groups(name, created_at, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(name) DO NOTHING
                    """,
                    (new_product_group_name.strip(), timestamp, timestamp),
                )
                row = conn.execute(
                    "SELECT id FROM catalog_product_groups WHERE name = ? COLLATE NOCASE",
                    (new_product_group_name.strip(),),
                ).fetchone()
                product_group_id = int(row["id"])
            product_id = self._ensure_catalog_product(
                conn,
                name=name,
                location_id=location_id,
                quantity_unit_id=quantity_unit_id,
                product_group_id=product_group_id,
                default_best_before_days=default_best_before_days,
            )
            conn.execute(
                """
                UPDATE catalog_products
                SET minimum_stock_quantity = ?, shopping_target_quantity = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    round(float(minimum_stock_quantity), 6),
                    round(float(shopping_target_quantity), 6),
                    timestamp,
                    product_id,
                ),
            )
            if brand or barcode:
                variant = conn.execute(
                    """
                    SELECT id FROM catalog_product_variants
                    WHERE product_id = ? AND COALESCE(brand, '') = ?
                    ORDER BY created_at LIMIT 1
                    """,
                    (product_id, (brand or "").strip()),
                ).fetchone()
                variant_id = str(variant["id"]) if variant else str(uuid.uuid4())
                timestamp = now_iso()
                if not variant:
                    conn.execute(
                        """
                        INSERT INTO catalog_product_variants(
                            id, product_id, brand, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (variant_id, product_id, (brand or "").strip() or None, timestamp, timestamp),
                    )
                if barcode:
                    conn.execute(
                        """
                        INSERT INTO catalog_barcodes(
                            barcode, variant_id, created_at, updated_at
                        ) VALUES (?, ?, ?, ?)
                        ON CONFLICT(barcode) DO UPDATE SET
                            variant_id = excluded.variant_id,
                            updated_at = excluded.updated_at
                        """,
                        (barcode.strip(), variant_id, timestamp, timestamp),
                    )
        product = self.get_catalog_product(product_id)
        if not product:
            raise RuntimeError("Das Produkt konnte nicht angelegt werden")
        return product

    def get_external_product(
        self, source: str, external_id: str, *, max_age_days: int = 30
    ) -> dict[str, Any] | None:
        cutoff = (datetime.now(UTC) - timedelta(days=max_age_days)).isoformat(timespec="seconds")
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT payload_json, fetched_at
                FROM catalog_external_refs
                WHERE source = ? AND external_id = ? AND fetched_at >= ?
                """,
                (source, external_id, cutoff),
            ).fetchone()
        if not row or not row["payload_json"]:
            return None
        try:
            payload = json.loads(str(row["payload_json"]))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def put_external_product(
        self,
        source: str,
        external_id: str,
        payload: dict[str, Any],
        *,
        source_url: str | None = None,
        license_name: str | None = None,
        attribution: str | None = None,
    ) -> None:
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO catalog_external_refs(
                    source, external_id, source_url, license, attribution,
                    payload_json, fetched_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    source_url = excluded.source_url,
                    license = excluded.license,
                    attribution = excluded.attribution,
                    payload_json = excluded.payload_json,
                    fetched_at = excluded.fetched_at,
                    updated_at = excluded.updated_at
                """,
                (
                    source,
                    external_id,
                    source_url,
                    license_name,
                    attribution,
                    json.dumps(payload, ensure_ascii=False),
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )

    def attach_external_candidate(
        self,
        *,
        product_id: str,
        source: str,
        external_id: str,
        candidate: dict[str, Any],
        variant_name: str | None = None,
        package_amount: float | None = None,
        package_unit: str | None = None,
    ) -> str:
        timestamp = now_iso()
        barcode = str(candidate.get("barcode") or external_id).strip()
        brand = str(candidate.get("brand") or "").strip() or None
        image_url = str(candidate.get("image_url") or "").strip() or None
        with self.connect() as conn:
            product = conn.execute(
                "SELECT id FROM catalog_products WHERE id = ? AND active = 1",
                (product_id,),
            ).fetchone()
            if not product:
                raise ValueError("Produkt nicht gefunden")
            existing_barcode = conn.execute(
                """
                SELECT v.id, v.product_id FROM catalog_barcodes b
                JOIN catalog_product_variants v ON v.id = b.variant_id
                WHERE b.barcode = ?
                """,
                (barcode,),
            ).fetchone() if barcode else None
            if existing_barcode and str(existing_barcode["product_id"]) != product_id:
                raise ValueError("Dieser Barcode gehört bereits zu einem anderen Produkt")
            if existing_barcode:
                variant_id = str(existing_barcode["id"])
            else:
                variant = conn.execute(
                    """
                    SELECT id FROM catalog_product_variants
                    WHERE product_id = ?
                      AND COALESCE(brand, '') = COALESCE(?, '')
                      AND COALESCE(package_amount, 0) = COALESCE(?, 0)
                      AND COALESCE(package_unit, '') = COALESCE(?, '')
                    ORDER BY created_at LIMIT 1
                    """,
                    (product_id, brand, package_amount, package_unit),
                ).fetchone()
                variant_id = str(variant["id"]) if variant else str(uuid.uuid4())
                if not variant:
                    conn.execute(
                        """
                        INSERT INTO catalog_product_variants(
                            id, product_id, name, brand, package_amount, package_unit,
                            image_url, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            variant_id,
                            product_id,
                            variant_name,
                            brand,
                            package_amount,
                            package_unit,
                            image_url,
                            timestamp,
                            timestamp,
                        ),
                    )
            conn.execute(
                """
                UPDATE catalog_product_variants
                SET name = COALESCE(NULLIF(name, ''), ?),
                    brand = COALESCE(NULLIF(brand, ''), ?),
                    package_amount = COALESCE(package_amount, ?),
                    package_unit = COALESCE(NULLIF(package_unit, ''), ?),
                    image_url = COALESCE(NULLIF(image_url, ''), ?),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    variant_name,
                    brand,
                    package_amount,
                    package_unit,
                    image_url,
                    timestamp,
                    variant_id,
                ),
            )
            conn.execute(
                """
                UPDATE catalog_products
                SET image_url = COALESCE(NULLIF(image_url, ''), ?), updated_at = ?
                WHERE id = ?
                """,
                (image_url, timestamp, product_id),
            )
            if barcode:
                conn.execute(
                    """
                    INSERT INTO catalog_barcodes(
                        barcode, variant_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(barcode) DO UPDATE SET
                        variant_id = excluded.variant_id,
                        updated_at = excluded.updated_at
                    """,
                    (barcode, variant_id, timestamp, timestamp),
                )
            conn.execute(
                """
                INSERT INTO catalog_external_refs(
                    source, external_id, product_id, variant_id, source_url,
                    license, attribution, payload_json, fetched_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    product_id = excluded.product_id,
                    variant_id = excluded.variant_id,
                    source_url = excluded.source_url,
                    license = excluded.license,
                    attribution = excluded.attribution,
                    payload_json = excluded.payload_json,
                    fetched_at = excluded.fetched_at,
                    updated_at = excluded.updated_at
                """,
                (
                    source,
                    external_id,
                    product_id,
                    variant_id,
                    candidate.get("source_url"),
                    candidate.get("database_license"),
                    candidate.get("attribution"),
                    json.dumps(candidate, ensure_ascii=False),
                    timestamp,
                    timestamp,
                    timestamp,
                ),
            )
        return variant_id

    def _scan_row(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        if not row:
            return None
        result = dict(row)
        for source, target in (("proposed_json", "suggestion"), ("result_json", "action_result")):
            raw = result.pop(source, None)
            try:
                parsed = json.loads(str(raw)) if raw else None
            except json.JSONDecodeError:
                parsed = None
            result[target] = parsed if isinstance(parsed, dict) else None
        return result

    def get_scan(self, scan_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT s.*,
                    p.name AS product_name,
                    p.image_url AS product_image_url,
                    p.default_location_id,
                    l.name AS default_location_name,
                    p.default_quantity_unit_id,
                    u.name AS default_quantity_unit_name,
                    v.brand,
                    v.name AS variant_name,
                    v.package_amount,
                    v.package_unit,
                    COALESCE((SELECT SUM(quantity) FROM stock_lots
                        WHERE product_id = p.id), 0) AS stock_quantity
                FROM scan_drafts s
                LEFT JOIN catalog_products p ON p.id = s.product_id
                LEFT JOIN catalog_product_variants v ON v.id = s.variant_id
                LEFT JOIN catalog_locations l ON l.id = p.default_location_id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                WHERE s.id = ?
                """,
                (scan_id,),
            ).fetchone()
        return self._scan_row(row)

    def create_scan(
        self,
        *,
        barcode_raw: str,
        barcode_normalized: str,
        symbology: str | None,
        mode: str,
        resolution_source: str,
        product_id: str | None = None,
        variant_id: str | None = None,
        suggestion: dict[str, Any] | None = None,
        upstream_error: str | None = None,
        resolve_key: str | None = None,
    ) -> dict[str, Any]:
        reuse_scan_id: str | None = None
        with self.connect() as conn:
            if resolve_key:
                existing = conn.execute(
                    "SELECT id FROM scan_drafts WHERE resolve_key = ?", (resolve_key,)
                ).fetchone()
                if existing:
                    reuse_scan_id = str(existing["id"])
            if not reuse_scan_id and not product_id:
                existing = conn.execute(
                    """
                    SELECT id FROM scan_drafts
                    WHERE barcode_normalized = ? AND mode = ? AND status = 'unresolved'
                    ORDER BY updated_at DESC LIMIT 1
                    """,
                    (barcode_normalized, mode),
                ).fetchone()
                if existing:
                    conn.execute(
                        """
                        UPDATE scan_drafts SET proposed_json = ?, upstream_error = ?,
                            resolution_source = ?, resolve_key = COALESCE(resolve_key, ?),
                            updated_at = ? WHERE id = ?
                        """,
                        (
                            json.dumps(suggestion or {}, ensure_ascii=False),
                            upstream_error,
                            resolution_source,
                            resolve_key,
                            now_iso(),
                            existing["id"],
                        ),
                    )
                    scan_id = str(existing["id"])
                    reuse_scan_id = scan_id
            if not reuse_scan_id:
                scan_id = str(uuid.uuid4())
                timestamp = now_iso()
                conn.execute(
                    """
                    INSERT INTO scan_drafts(
                        id, barcode_raw, barcode_normalized, symbology, mode, status,
                        resolution_source, product_id, variant_id, proposed_json,
                        upstream_error, resolve_key, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        scan_id,
                        barcode_raw,
                        barcode_normalized,
                        symbology,
                        mode,
                        "resolved" if product_id else "unresolved",
                        resolution_source,
                        product_id,
                        variant_id,
                        json.dumps(suggestion or {}, ensure_ascii=False),
                        upstream_error,
                        resolve_key,
                        timestamp,
                        timestamp,
                    ),
                )
                reuse_scan_id = scan_id
        return self.get_scan(str(reuse_scan_id)) or {}

    def list_unresolved_scans(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM scan_drafts
                WHERE status = 'unresolved'
                ORDER BY updated_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._scan_row(row) or {} for row in rows]

    def update_scan(
        self,
        scan_id: str,
        *,
        mode: str | None = None,
        product_id: str | None = None,
        suggestion_updates: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        current = self.get_scan(scan_id)
        if not current or current["status"] in {"confirmed", "discarded"}:
            return None
        suggestion = dict(current.get("suggestion") or {})
        suggestion.update({key: value for key, value in (suggestion_updates or {}).items() if value is not None})
        with self.connect() as conn:
            variant_id = current.get("variant_id")
            if product_id:
                variant = conn.execute(
                    """
                    SELECT v.id FROM catalog_barcodes b
                    JOIN catalog_product_variants v ON v.id = b.variant_id
                    WHERE b.barcode = ? AND v.product_id = ?
                    """,
                    (current["barcode_normalized"], product_id),
                ).fetchone()
                variant_id = str(variant["id"]) if variant else None
            conn.execute(
                """
                UPDATE scan_drafts SET mode = COALESCE(?, mode),
                    product_id = COALESCE(?, product_id), variant_id = ?,
                    status = CASE WHEN COALESCE(?, product_id) IS NULL
                        THEN 'unresolved' ELSE 'resolved' END,
                    resolution_source = CASE WHEN ? IS NULL
                        THEN resolution_source ELSE 'local' END,
                    proposed_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    mode,
                    product_id,
                    variant_id,
                    product_id,
                    product_id,
                    json.dumps(suggestion, ensure_ascii=False),
                    now_iso(),
                    scan_id,
                ),
            )
        return self.get_scan(scan_id)

    def ensure_scan_product(
        self,
        scan_id: str,
        *,
        name: str,
        product_id: str | None = None,
        brand: str | None = None,
        variant_name: str | None = None,
        package_amount: float | None = None,
        package_unit: str | None = None,
        image_url: str | None = None,
        location_id: int | None = None,
        quantity_unit_id: int | None = None,
        product_group_id: int | None = None,
        default_best_before_days: int = 0,
    ) -> dict[str, Any]:
        scan = self.get_scan(scan_id)
        if not scan:
            raise KeyError("Scan nicht gefunden")
        timestamp = now_iso()
        with self.connect() as conn:
            if product_id:
                product = conn.execute(
                    "SELECT id FROM catalog_products WHERE id = ? AND active = 1",
                    (product_id,),
                ).fetchone()
                if not product:
                    raise KeyError("Produkt nicht gefunden")
                resolved_product_id = str(product["id"])
            else:
                resolved_product_id = self._ensure_catalog_product(
                    conn,
                    name=name,
                    location_id=location_id,
                    quantity_unit_id=quantity_unit_id,
                    product_group_id=product_group_id,
                    default_best_before_days=default_best_before_days,
                )
            if image_url:
                conn.execute(
                    """
                    UPDATE catalog_products SET image_url = COALESCE(image_url, ?),
                        updated_at = ? WHERE id = ?
                    """,
                    (image_url, timestamp, resolved_product_id),
                )
            variant = conn.execute(
                """
                SELECT v.id FROM catalog_barcodes b
                JOIN catalog_product_variants v ON v.id = b.variant_id
                WHERE b.barcode = ?
                """,
                (scan["barcode_normalized"],),
            ).fetchone()
            if variant:
                variant_id = str(variant["id"])
                conn.execute(
                    """
                    UPDATE catalog_product_variants SET product_id = ?,
                        name = COALESCE(?, name), brand = COALESCE(?, brand),
                        package_amount = COALESCE(?, package_amount),
                        package_unit = COALESCE(?, package_unit),
                        image_url = COALESCE(?, image_url), updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        resolved_product_id,
                        variant_name,
                        brand,
                        package_amount,
                        package_unit,
                        image_url,
                        timestamp,
                        variant_id,
                    ),
                )
            else:
                variant_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO catalog_product_variants(
                        id, product_id, name, brand, package_amount,
                        package_unit, image_url, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        variant_id,
                        resolved_product_id,
                        variant_name,
                        brand,
                        package_amount,
                        package_unit,
                        image_url,
                        timestamp,
                        timestamp,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO catalog_barcodes(
                        barcode, variant_id, symbology, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        scan["barcode_normalized"],
                        variant_id,
                        scan.get("symbology"),
                        timestamp,
                        timestamp,
                    ),
                )
            if scan["resolution_source"] in {"cache", "open_facts"}:
                conn.execute(
                    """
                    UPDATE catalog_external_refs SET product_id = ?, variant_id = ?,
                        updated_at = ?
                    WHERE source = 'open_facts' AND external_id = ?
                    """,
                    (resolved_product_id, variant_id, timestamp, scan["barcode_normalized"]),
                )
            conn.execute(
                """
                UPDATE scan_drafts SET product_id = ?, variant_id = ?,
                    status = 'resolved', updated_at = ? WHERE id = ?
                """,
                (resolved_product_id, variant_id, timestamp, scan_id),
            )
        return self.get_scan(scan_id) or {}

    def confirm_scan_action(
        self,
        scan_id: str,
        *,
        confirmation_key: str,
        quantity: float,
        location_id: int | None = None,
        best_before_date: str | None = None,
        unit_price: float | None = None,
        result_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self.connect() as conn:
            key_owner = conn.execute(
                "SELECT id FROM scan_drafts WHERE confirmation_key = ?",
                (confirmation_key,),
            ).fetchone()
            if key_owner and str(key_owner["id"]) != scan_id:
                raise ValueError("Diese Bestätigungskennung wurde bereits verwendet")
            scan = conn.execute("SELECT * FROM scan_drafts WHERE id = ?", (scan_id,)).fetchone()
            if not scan:
                raise KeyError("Scan nicht gefunden")
            if scan["status"] == "confirmed":
                if scan["confirmation_key"] == confirmation_key:
                    return self.get_scan(scan_id) or {}
                raise ValueError("Dieser Scan wurde bereits bestätigt")
            if scan["status"] == "discarded":
                raise ValueError("Dieser Scan wurde verworfen")
            product_id = str(scan["product_id"] or "")
            if not product_id:
                raise ValueError("Bitte zuerst ein Produkt zuordnen")
            mode = str(scan["mode"])
            timestamp = now_iso()
            resolved_location_id = location_id
            if resolved_location_id is None:
                product = conn.execute(
                    "SELECT default_location_id FROM catalog_products WHERE id = ?",
                    (product_id,),
                ).fetchone()
                resolved_location_id = product["default_location_id"] if product else None
            result: dict[str, Any] = {"mode": mode, "quantity": quantity}
            result.update(result_metadata or {})
            if mode == "add":
                lot_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO stock_lots(
                        id, product_id, variant_id, location_id, quantity,
                        best_before_date, unit_price, purchased_date,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        lot_id,
                        product_id,
                        scan["variant_id"],
                        resolved_location_id,
                        quantity,
                        best_before_date,
                        unit_price,
                        timestamp[:10],
                        timestamp,
                        timestamp,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO stock_movements(
                        id, product_id, variant_id, lot_id, location_id,
                        movement_type, quantity_delta, source, reference_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'scan_add', ?, 'scanner', ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        product_id,
                        scan["variant_id"],
                        lot_id,
                        resolved_location_id,
                        quantity,
                        scan_id,
                        timestamp,
                    ),
                )
                result.update({"lot_id": lot_id, "location_id": resolved_location_id})
            elif mode == "consume":
                lots = conn.execute(
                    """
                    SELECT * FROM stock_lots
                    WHERE product_id = ? AND quantity > 0
                    ORDER BY best_before_date IS NULL, best_before_date, created_at
                    """,
                    (product_id,),
                ).fetchall()
                available = sum(float(lot["quantity"]) for lot in lots)
                if available + 1e-9 < quantity:
                    raise ValueError(f"Nur {available:g} im Bestand")
                remaining = quantity
                movement_ids: list[str] = []
                for lot in lots:
                    if remaining <= 1e-9:
                        break
                    taken = min(float(lot["quantity"]), remaining)
                    conn.execute(
                        "UPDATE stock_lots SET quantity = quantity - ?, updated_at = ? WHERE id = ?",
                        (taken, timestamp, lot["id"]),
                    )
                    movement_id = str(uuid.uuid4())
                    movement_ids.append(movement_id)
                    conn.execute(
                        """
                        INSERT INTO stock_movements(
                            id, product_id, variant_id, lot_id, location_id,
                            movement_type, quantity_delta, source, reference_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'scan_consume', ?, 'scanner', ?, ?)
                        """,
                        (
                            movement_id,
                            product_id,
                            lot["variant_id"],
                            lot["id"],
                            lot["location_id"],
                            -taken,
                            scan_id,
                            timestamp,
                        ),
                    )
                    remaining -= taken
                result["movement_ids"] = movement_ids
            elif mode == "open":
                lot = conn.execute(
                    """
                    SELECT * FROM stock_lots
                    WHERE product_id = ? AND quantity > 0 AND opened_at IS NULL
                    ORDER BY best_before_date IS NULL, best_before_date, created_at LIMIT 1
                    """,
                    (product_id,),
                ).fetchone()
                if not lot:
                    raise ValueError("Kein ungeöffnetes Paket im Bestand")
                conn.execute(
                    "UPDATE stock_lots SET opened_at = ?, updated_at = ? WHERE id = ?",
                    (timestamp, timestamp, lot["id"]),
                )
                conn.execute(
                    """
                    INSERT INTO stock_movements(
                        id, product_id, variant_id, lot_id, location_id,
                        movement_type, quantity_delta, source, reference_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'scan_open', 0, 'scanner', ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        product_id,
                        lot["variant_id"],
                        lot["id"],
                        lot["location_id"],
                        scan_id,
                        timestamp,
                    ),
                )
                result.update({"lot_id": str(lot["id"]), "opened_at": timestamp})
            elif mode == "shopping":
                product = conn.execute(
                    "SELECT name FROM catalog_products WHERE id = ?", (product_id,)
                ).fetchone()
                existing = conn.execute(
                    """
                    SELECT id FROM shopping_list_items
                    WHERE product_id = ? AND checked = 0 ORDER BY created_at LIMIT 1
                    """,
                    (product_id,),
                ).fetchone()
                if existing:
                    item_id = str(existing["id"])
                    conn.execute(
                        """
                        UPDATE shopping_list_items
                        SET desired_quantity = desired_quantity + ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (quantity, timestamp, item_id),
                    )
                else:
                    item_id = str(uuid.uuid4())
                    conn.execute(
                        """
                        INSERT INTO shopping_list_items(
                            id, product_id, label, desired_quantity, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (item_id, product_id, str(product["name"]), quantity, timestamp, timestamp),
                    )
                result["shopping_item_id"] = item_id
            elif mode != "identify":
                raise ValueError("Unbekannter Scan-Modus")
            conn.execute(
                """
                UPDATE scan_drafts SET status = 'confirmed', confirmation_key = ?,
                    result_json = ?, updated_at = ? WHERE id = ?
                """,
                (confirmation_key, json.dumps(result, ensure_ascii=False), timestamp, scan_id),
            )
        return self.get_scan(scan_id) or {}

    def discard_scan(self, scan_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT status FROM scan_drafts WHERE id = ?", (scan_id,)
            ).fetchone()
            if not row or row["status"] == "confirmed":
                return None
            conn.execute(
                "UPDATE scan_drafts SET status = 'discarded', updated_at = ? WHERE id = ?",
                (now_iso(), scan_id),
            )
        return self.get_scan(scan_id)

    def stock_count_products(self, query: str = "") -> list[dict[str, Any]]:
        products = self.list_catalog_products(query, limit=10000)
        return [
            detail
            for product in products
            if (detail := self.get_catalog_product_detail(str(product["id"])))
        ]

    def get_stock_count_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM stock_count_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not session:
                return None
            lines = conn.execute(
                """
                SELECT l.*, p.name AS product_name,
                    u.name AS quantity_unit_name,
                    loc.name AS location_name,
                    v.name AS variant_name,
                    v.brand AS variant_brand
                FROM stock_count_lines l
                JOIN catalog_products p ON p.id = l.product_id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                LEFT JOIN catalog_locations loc ON loc.id = l.location_id
                LEFT JOIN catalog_product_variants v ON v.id = l.variant_id
                WHERE l.session_id = ?
                ORDER BY p.name COLLATE NOCASE
                """,
                (session_id,),
            ).fetchall()
        return {**dict(session), "lines": [dict(line) for line in lines]}

    def list_stock_count_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id FROM stock_count_sessions
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            session
            for row in rows
            if (session := self.get_stock_count_session(str(row["id"])))
        ]

    def apply_stock_count(
        self,
        *,
        client_mutation_id: str,
        source: str,
        note: str,
        lines: list[dict[str, Any]],
    ) -> dict[str, Any]:
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT id FROM stock_count_sessions WHERE client_mutation_id = ?",
                (client_mutation_id,),
            ).fetchone()
        if existing:
            result = self.get_stock_count_session(str(existing["id"]))
            if not result:
                raise RuntimeError("Die vorhandene Zählung konnte nicht geladen werden")
            return result
        if not lines:
            raise ValueError("Bitte mindestens ein Produkt zählen")
        product_ids = [str(line["product_id"]) for line in lines]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Jedes Produkt darf pro Zählung nur einmal vorkommen")

        session_id = str(uuid.uuid4())
        timestamp = now_iso()
        changed_count = 0
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO stock_count_sessions(
                    id, client_mutation_id, source, note, status,
                    line_count, changed_count, created_at
                ) VALUES (?, ?, ?, ?, 'confirmed', 0, 0, ?)
                """,
                (session_id, client_mutation_id, source, note.strip(), timestamp),
            )
            for line in lines:
                product_id = str(line["product_id"])
                product = conn.execute(
                    """
                    SELECT id, default_location_id FROM catalog_products
                    WHERE id = ? AND active = 1
                    """,
                    (product_id,),
                ).fetchone()
                if not product:
                    raise KeyError("Produkt nicht gefunden")
                variant_id = line.get("variant_id")
                if variant_id:
                    variant = conn.execute(
                        """
                        SELECT id FROM catalog_product_variants
                        WHERE id = ? AND product_id = ?
                        """,
                        (variant_id, product_id),
                    ).fetchone()
                    if not variant:
                        raise ValueError("Die Variante gehört nicht zu diesem Produkt")
                location_id = line.get("location_id") or product["default_location_id"]
                if location_id is not None:
                    self._require_active_master(
                        conn, "catalog_locations", int(location_id), "Lagerort"
                    )
                current_row = conn.execute(
                    """
                    SELECT COALESCE(SUM(quantity), 0) AS quantity
                    FROM stock_lots WHERE product_id = ?
                    """,
                    (product_id,),
                ).fetchone()
                previous = round(float(current_row["quantity"] or 0), 6)
                counted = round(float(line["counted_quantity"]), 6)
                delta = round(counted - previous, 6)
                movement_count = 0

                if delta > 1e-9:
                    lot_id = str(uuid.uuid4())
                    conn.execute(
                        """
                        INSERT INTO stock_lots(
                            id, product_id, variant_id, location_id, quantity,
                            best_before_date, unit_price, purchased_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                        """,
                        (
                            lot_id,
                            product_id,
                            variant_id,
                            location_id,
                            delta,
                            line.get("best_before_date"),
                            line.get("unit_price"),
                            timestamp,
                            timestamp,
                        ),
                    )
                    conn.execute(
                        """
                        INSERT INTO stock_movements(
                            id, product_id, variant_id, lot_id, location_id,
                            movement_type, quantity_delta, source, reference_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'stock_count_increase', ?, 'stock_count', ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            product_id,
                            variant_id,
                            lot_id,
                            location_id,
                            delta,
                            session_id,
                            timestamp,
                        ),
                    )
                    movement_count = 1
                elif delta < -1e-9:
                    remaining = -delta
                    lots = conn.execute(
                        """
                        SELECT * FROM stock_lots
                        WHERE product_id = ? AND quantity > 0
                        ORDER BY best_before_date IS NULL, best_before_date, created_at
                        """,
                        (product_id,),
                    ).fetchall()
                    for lot in lots:
                        if remaining <= 1e-9:
                            break
                        taken = min(float(lot["quantity"]), remaining)
                        conn.execute(
                            """
                            UPDATE stock_lots SET quantity = quantity - ?, updated_at = ?
                            WHERE id = ?
                            """,
                            (taken, timestamp, lot["id"]),
                        )
                        conn.execute(
                            """
                            INSERT INTO stock_movements(
                                id, product_id, variant_id, lot_id, location_id,
                                movement_type, quantity_delta, source, reference_id, created_at
                            ) VALUES (?, ?, ?, ?, ?, 'stock_count_decrease', ?, 'stock_count', ?, ?)
                            """,
                            (
                                str(uuid.uuid4()),
                                product_id,
                                lot["variant_id"],
                                lot["id"],
                                lot["location_id"],
                                -taken,
                                session_id,
                                timestamp,
                            ),
                        )
                        movement_count += 1
                        remaining -= taken
                    if remaining > 1e-6:
                        raise RuntimeError("Der vorhandene Bestand hat sich während der Zählung geändert")

                if abs(delta) > 1e-9:
                    changed_count += 1
                conn.execute(
                    """
                    INSERT INTO stock_count_lines(
                        id, session_id, product_id, variant_id, location_id,
                        previous_quantity, counted_quantity, quantity_delta,
                        best_before_date, unit_price, note, movement_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        session_id,
                        product_id,
                        variant_id,
                        location_id,
                        previous,
                        counted,
                        delta,
                        line.get("best_before_date"),
                        line.get("unit_price"),
                        str(line.get("note") or "").strip(),
                        movement_count,
                        timestamp,
                    ),
                )
            conn.execute(
                """
                UPDATE stock_count_sessions SET line_count = ?, changed_count = ?
                WHERE id = ?
                """,
                (len(lines), changed_count, session_id),
            )
        result = self.get_stock_count_session(session_id)
        if not result:
            raise RuntimeError("Die Zählung konnte nicht geladen werden")
        return result

    def grocy_stock_preview(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        grouped: dict[int, dict[str, Any]] = {}
        for entry in entries:
            nested_product = entry.get("product") if isinstance(entry.get("product"), dict) else {}
            raw_id = entry.get("product_id") or nested_product.get("id")
            try:
                grocy_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            group = grouped.setdefault(
                grocy_id,
                {"amounts": [], "aggregated": [], "dates": [], "name": nested_product.get("name")},
            )
            aggregated = entry.get("amount_aggregated")
            if aggregated is None:
                aggregated = entry.get("amount_total")
            amount = entry.get("amount")
            try:
                if aggregated is not None:
                    group["aggregated"].append(float(aggregated))
                elif amount is not None:
                    group["amounts"].append(float(amount))
            except (TypeError, ValueError):
                pass
            date_value = str(entry.get("best_before_date") or "")
            if date_value and not date_value.startswith("2999-"):
                group["dates"].append(date_value)
            group["name"] = group["name"] or entry.get("product_name")

        local_products = self.list_catalog_products(limit=10000)
        mapped_ids = {
            int(product["grocy_product_id"]): product
            for product in local_products
            if product.get("grocy_product_id") is not None
        }
        items: list[dict[str, Any]] = []
        for grocy_id, product in mapped_ids.items():
            group = grouped.get(grocy_id, {})
            aggregated = group.get("aggregated", [])
            proposed = max(aggregated) if aggregated else sum(group.get("amounts", []))
            proposed = round(float(proposed), 6)
            current = round(float(product.get("stock_quantity") or 0), 6)
            items.append(
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "grocy_product_id": grocy_id,
                    "current_quantity": current,
                    "proposed_quantity": proposed,
                    "quantity_delta": round(proposed - current, 6),
                    "default_location_id": product.get("default_location_id"),
                    "default_location_name": product.get("default_location_name"),
                    "quantity_unit_name": product.get("default_quantity_unit_name"),
                    "best_before_date": min(group.get("dates", []), default=None),
                }
            )
        items.sort(key=lambda item: str(item["product_name"]).casefold())
        unmapped = []
        for grocy_id, group in grouped.items():
            if grocy_id in mapped_ids:
                continue
            aggregated = group.get("aggregated", [])
            quantity = max(aggregated) if aggregated else sum(group.get("amounts", []))
            if abs(quantity) > 1e-9:
                unmapped.append(
                    {
                        "grocy_product_id": grocy_id,
                        "product_name": group.get("name"),
                        "quantity": round(float(quantity), 6),
                    }
                )
        return {
            "items": items,
            "unmapped": unmapped,
            "generated_at": now_iso(),
        }

    def list_shopping_items(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT s.*, p.name AS product_name, p.image_url AS product_image_url,
                    p.minimum_stock_quantity, p.shopping_target_quantity,
                    u.name AS quantity_unit_name,
                    COALESCE((SELECT SUM(l.quantity) FROM stock_lots l
                        WHERE l.product_id = p.id), 0) AS stock_quantity
                FROM shopping_list_items s
                LEFT JOIN catalog_products p ON p.id = s.product_id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                WHERE s.checked = 0
                ORDER BY s.updated_at DESC, s.created_at
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_shopping_item(self, item_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT s.*, p.name AS product_name, p.image_url AS product_image_url,
                    p.minimum_stock_quantity, p.shopping_target_quantity,
                    u.name AS quantity_unit_name,
                    COALESCE((SELECT SUM(l.quantity) FROM stock_lots l
                        WHERE l.product_id = p.id), 0) AS stock_quantity
                FROM shopping_list_items s
                LEFT JOIN catalog_products p ON p.id = s.product_id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                WHERE s.id = ?
                """,
                (item_id,),
            ).fetchone()
        return dict(row) if row else None

    def low_stock_preview(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                WITH product_stock AS (
                    SELECT p.id AS product_id, COALESCE(SUM(l.quantity), 0) AS quantity
                    FROM catalog_products p
                    LEFT JOIN stock_lots l ON l.product_id = p.id
                    GROUP BY p.id
                )
                SELECT p.id AS product_id, p.name AS product_name,
                    p.image_url AS product_image_url,
                    ps.quantity AS current_quantity,
                    p.minimum_stock_quantity AS minimum_quantity,
                    p.shopping_target_quantity AS target_quantity,
                    ROUND(p.shopping_target_quantity - ps.quantity, 6) AS suggested_quantity,
                    u.name AS quantity_unit_name,
                    s.id AS existing_item_id,
                    s.desired_quantity AS existing_desired_quantity
                FROM catalog_products p
                JOIN product_stock ps ON ps.product_id = p.id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                LEFT JOIN shopping_list_items s
                    ON s.product_id = p.id AND s.checked = 0
                WHERE p.active = 1
                  AND p.shopping_target_quantity > 0
                  AND p.shopping_target_quantity > ps.quantity
                  AND ps.quantity <= p.minimum_stock_quantity
                ORDER BY p.name COLLATE NOCASE
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_shopping_generation_run(self, run_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            run = conn.execute(
                "SELECT * FROM shopping_generation_runs WHERE id = ?", (run_id,)
            ).fetchone()
            if not run:
                return None
            items = conn.execute(
                """
                SELECT i.*, p.name AS product_name, u.name AS quantity_unit_name
                FROM shopping_generation_items i
                JOIN catalog_products p ON p.id = i.product_id
                LEFT JOIN catalog_quantity_units u ON u.id = p.default_quantity_unit_id
                WHERE i.run_id = ?
                ORDER BY p.name COLLATE NOCASE
                """,
                (run_id,),
            ).fetchall()
        return {**dict(run), "items": [dict(item) for item in items]}

    def generate_shopping_list(
        self, *, client_mutation_id: str, product_ids: list[str]
    ) -> dict[str, Any]:
        with self.connect() as conn:
            existing_run = conn.execute(
                "SELECT id FROM shopping_generation_runs WHERE client_mutation_id = ?",
                (client_mutation_id,),
            ).fetchone()
        if existing_run:
            result = self.get_shopping_generation_run(str(existing_run["id"]))
            if not result:
                raise RuntimeError("Die vorhandene Einkaufslisten-Erzeugung fehlt")
            return result
        if not product_ids:
            raise ValueError("Bitte mindestens einen Nachkauf auswählen")
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Jedes Produkt darf nur einmal ausgewählt werden")

        run_id = str(uuid.uuid4())
        timestamp = now_iso()
        counts = {"created": 0, "updated": 0, "unchanged": 0, "skipped": 0}
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO shopping_generation_runs(
                    id, client_mutation_id, requested_count, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (run_id, client_mutation_id, len(product_ids), timestamp),
            )
            for product_id in product_ids:
                product = conn.execute(
                    """
                    SELECT p.id, p.name, p.minimum_stock_quantity,
                        p.shopping_target_quantity,
                        COALESCE((SELECT SUM(l.quantity) FROM stock_lots l
                            WHERE l.product_id = p.id), 0) AS current_quantity
                    FROM catalog_products p
                    WHERE p.id = ? AND p.active = 1
                    """,
                    (product_id,),
                ).fetchone()
                if not product:
                    raise KeyError("Produkt nicht gefunden")
                current = round(float(product["current_quantity"] or 0), 6)
                minimum = round(float(product["minimum_stock_quantity"] or 0), 6)
                target = round(float(product["shopping_target_quantity"] or 0), 6)
                suggested = round(max(0.0, target - current), 6)
                eligible = target > 0 and target > current and current <= minimum
                shopping_item_id: str | None = None
                action = "skipped"
                if eligible:
                    existing = conn.execute(
                        """
                        SELECT * FROM shopping_list_items
                        WHERE product_id = ? AND checked = 0
                        ORDER BY updated_at DESC LIMIT 1
                        """,
                        (product_id,),
                    ).fetchone()
                    if existing:
                        shopping_item_id = str(existing["id"])
                        if float(existing["desired_quantity"]) + 1e-9 < suggested:
                            conn.execute(
                                """
                                UPDATE shopping_list_items
                                SET desired_quantity = ?, updated_at = ? WHERE id = ?
                                """,
                                (suggested, timestamp, shopping_item_id),
                            )
                            action = "updated"
                        else:
                            action = "unchanged"
                    else:
                        shopping_item_id = str(uuid.uuid4())
                        conn.execute(
                            """
                            INSERT INTO shopping_list_items(
                                id, product_id, label, desired_quantity, checked,
                                notes, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, 0, '', ?, ?)
                            """,
                            (
                                shopping_item_id,
                                product_id,
                                product["name"],
                                suggested,
                                timestamp,
                                timestamp,
                            ),
                        )
                        action = "created"
                counts[action] += 1
                conn.execute(
                    """
                    INSERT INTO shopping_generation_items(
                        id, run_id, product_id, shopping_item_id,
                        current_quantity, minimum_quantity, target_quantity,
                        suggested_quantity, action, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        run_id,
                        product_id,
                        shopping_item_id,
                        current,
                        minimum,
                        target,
                        suggested,
                        action,
                        timestamp,
                    ),
                )
            conn.execute(
                """
                UPDATE shopping_generation_runs
                SET created_count = ?, updated_count = ?, unchanged_count = ?,
                    skipped_count = ? WHERE id = ?
                """,
                (
                    counts["created"],
                    counts["updated"],
                    counts["unchanged"],
                    counts["skipped"],
                    run_id,
                ),
            )
        result = self.get_shopping_generation_run(run_id)
        if not result:
            raise RuntimeError("Die Einkaufsliste konnte nicht erzeugt werden")
        return result

    def update_shopping_item(
        self,
        item_id: str,
        *,
        desired_quantity: float,
        checked: bool,
        notes: str,
        expected_updated_at: str,
    ) -> dict[str, Any]:
        with self.connect() as conn:
            current = conn.execute(
                "SELECT * FROM shopping_list_items WHERE id = ?", (item_id,)
            ).fetchone()
            if not current:
                raise KeyError("Listeneintrag nicht gefunden")
            if str(current["updated_at"]) != expected_updated_at:
                raise RuntimeError("Der Listeneintrag wurde inzwischen geändert. Bitte neu laden.")
            timestamp = now_iso()
            conn.execute(
                """
                UPDATE shopping_list_items
                SET desired_quantity = ?, checked = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    round(float(desired_quantity), 6),
                    int(checked),
                    notes.strip(),
                    timestamp,
                    item_id,
                ),
            )
        result = self.get_shopping_item(item_id)
        if not result:
            raise RuntimeError("Der Listeneintrag konnte nicht geladen werden")
        return result

    def upsert_grocy_product(self, grocy_id: int, name: str) -> dict[str, Any]:
        with self.connect() as conn:
            product_id = self._ensure_catalog_product(
                conn,
                name=name,
                grocy_id=grocy_id,
            )
        product = self.get_catalog_product(product_id)
        if not product:
            raise RuntimeError("Das Grocy-Produkt konnte nicht in den Katalog übernommen werden")
        return product

    def import_grocy_catalog(
        self,
        master_data: dict[str, list[dict[str, Any]]],
        products: list[dict[str, Any]],
    ) -> dict[str, int]:
        counts = {"locations": 0, "quantity_units": 0, "product_groups": 0, "products": 0}
        timestamp = now_iso()
        with self.connect() as conn:
            for row in master_data.get("locations", []):
                if int(row.get("active", 1)) != 1:
                    continue
                conn.execute(
                    """
                    INSERT INTO catalog_locations(
                        name, description, is_freezer, active, grocy_id, created_at, updated_at
                    ) VALUES (?, ?, ?, 1, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        description = excluded.description,
                        is_freezer = excluded.is_freezer,
                        grocy_id = excluded.grocy_id,
                        updated_at = excluded.updated_at
                    """,
                    (
                        str(row.get("name", "")).strip(),
                        str(row.get("description", "")),
                        int(row.get("is_freezer", 0)),
                        int(row["id"]),
                        timestamp,
                        timestamp,
                    ),
                )
                counts["locations"] += 1
            for row in master_data.get("quantity_units", []):
                if int(row.get("active", 1)) != 1:
                    continue
                conn.execute(
                    """
                    INSERT INTO catalog_quantity_units(
                        name, name_plural, description, active, grocy_id, created_at, updated_at
                    ) VALUES (?, ?, ?, 1, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        name_plural = excluded.name_plural,
                        description = excluded.description,
                        grocy_id = excluded.grocy_id,
                        updated_at = excluded.updated_at
                    """,
                    (
                        str(row.get("name", "")).strip(),
                        str(row.get("name_plural") or row.get("name", "")).strip(),
                        str(row.get("description", "")),
                        int(row["id"]),
                        timestamp,
                        timestamp,
                    ),
                )
                counts["quantity_units"] += 1
            for row in master_data.get("product_groups", []):
                if int(row.get("active", 1)) != 1:
                    continue
                conn.execute(
                    """
                    INSERT INTO catalog_product_groups(
                        name, description, active, grocy_id, created_at, updated_at
                    ) VALUES (?, ?, 1, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        description = excluded.description,
                        grocy_id = excluded.grocy_id,
                        updated_at = excluded.updated_at
                    """,
                    (
                        str(row.get("name", "")).strip(),
                        str(row.get("description", "")),
                        int(row["id"]),
                        timestamp,
                        timestamp,
                    ),
                )
                counts["product_groups"] += 1

            location_by_grocy = {
                int(row["grocy_id"]): int(row["id"])
                for row in conn.execute(
                    "SELECT id, grocy_id FROM catalog_locations WHERE grocy_id IS NOT NULL"
                )
            }
            unit_by_grocy = {
                int(row["grocy_id"]): int(row["id"])
                for row in conn.execute(
                    "SELECT id, grocy_id FROM catalog_quantity_units WHERE grocy_id IS NOT NULL"
                )
            }
            group_by_grocy = {
                int(row["grocy_id"]): int(row["id"])
                for row in conn.execute(
                    "SELECT id, grocy_id FROM catalog_product_groups WHERE grocy_id IS NOT NULL"
                )
            }
            for row in products:
                if int(row.get("active", 1)) != 1 or not str(row.get("name", "")).strip():
                    continue
                self._ensure_catalog_product(
                    conn,
                    name=str(row["name"]),
                    grocy_id=int(row["id"]),
                    location_id=location_by_grocy.get(int(row.get("location_id") or 0)),
                    quantity_unit_id=unit_by_grocy.get(
                        int(row.get("qu_id_stock") or row.get("qu_id_purchase") or 0)
                    ),
                    product_group_id=group_by_grocy.get(int(row.get("product_group_id") or 0)),
                    default_best_before_days=int(row.get("default_best_before_days") or 0),
                )
                counts["products"] += 1
        return counts

    def get_catalog_mapping(self, store_name: str | None, raw_name: str) -> dict[str, Any] | None:
        store_key = retailer_key(store_name or "*")
        raw_key = canonical_receipt_key(raw_name)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT m.*, p.name AS product_name
                FROM catalog_product_mappings m
                JOIN catalog_products p ON p.id = m.product_id
                WHERE m.raw_key = ? AND m.store_key IN (?, '*')
                ORDER BY CASE WHEN m.store_key = ? THEN 0 ELSE 1 END
                LIMIT 1
                """,
                (raw_key, store_key, store_key),
            ).fetchone()
        return dict(row) if row else None

    def get_catalog_alias(self, raw_name: str, normalized_name: str | None) -> dict[str, Any] | None:
        keys = {canonical_receipt_key(raw_name), canonical_receipt_key(normalized_name or "")}
        keys.discard("")
        if not keys:
            return None
        key_values = sorted(keys)
        key_values.extend([""] * (2 - len(key_values)))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT a.product_id, p.name AS product_name
                FROM catalog_aliases a
                JOIN catalog_products p ON p.id = a.product_id
                WHERE a.alias_key IN (?, ?)
                GROUP BY a.product_id, p.name
                """,
                tuple(key_values),
            ).fetchall()
        products = {str(row["product_id"]): dict(row) for row in rows}
        return next(iter(products.values())) if len(products) == 1 else None

    def create_receipt(
        self,
        receipt: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> None:
        timestamp = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO receipts(
                    id, store_name, purchase_date, currency, total, status,
                    image_path, source_sha256, receipt_fingerprint, analysis_version,
                    retailer, store_number, store_address, grocy_store_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt["id"],
                    receipt.get("store_name"),
                    receipt.get("purchase_date"),
                    receipt.get("currency", "EUR"),
                    receipt.get("total"),
                    receipt.get("status", "review"),
                    receipt.get("image_path"),
                    receipt.get("source_sha256"),
                    receipt.get("receipt_fingerprint"),
                    receipt.get("analysis_version"),
                    receipt.get("retailer"),
                    receipt.get("store_number"),
                    receipt.get("store_address"),
                    receipt.get("grocy_store_id"),
                    timestamp,
                    timestamp,
                ),
            )
            for position, item in enumerate(items):
                conn.execute(
                    """
                    INSERT INTO receipt_items(
                        id, receipt_id, position, raw_name, normalized_name,
                        quantity, unit_price, total_price, barcode,
                        brand, best_before_date, suggested_location, suggested_unit,
                        suggested_product_group, suggested_best_before_days,
                        suggestion_confidence,
                        catalog_product_id, catalog_product_name, catalog_variant_id,
                        match_reason, match_evidence_json,
                        grocy_product_id, grocy_product_name, match_status,
                        match_score, suggested_product_id, suggested_product_name,
                        suggested_product_score, suggested_catalog_product_id,
                        suggested_catalog_product_name, suggested_catalog_product_score,
                        imported, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    """,
                    (
                        item["id"],
                        receipt["id"],
                        position,
                        item["raw_name"],
                        item.get("normalized_name"),
                        item.get("quantity", 1),
                        item.get("unit_price"),
                        item.get("total_price"),
                        item.get("barcode"),
                        item.get("brand"),
                        item.get("best_before_date"),
                        item.get("suggested_location"),
                        item.get("suggested_unit"),
                        item.get("suggested_product_group"),
                        item.get("suggested_best_before_days"),
                        item.get("suggestion_confidence"),
                        item.get("catalog_product_id"),
                        item.get("catalog_product_name"),
                        item.get("catalog_variant_id"),
                        item.get("match_reason"),
                        json.dumps(item.get("match_evidence") or [], ensure_ascii=False),
                        item.get("grocy_product_id"),
                        item.get("grocy_product_name"),
                        item.get("match_status", "unresolved"),
                        item.get("match_score"),
                        item.get("suggested_product_id"),
                        item.get("suggested_product_name"),
                        item.get("suggested_product_score"),
                        item.get("suggested_catalog_product_id"),
                        item.get("suggested_catalog_product_name"),
                        item.get("suggested_catalog_product_score"),
                        timestamp,
                        timestamp,
                    ),
                )

    def list_receipts(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT r.*,
                    COUNT(i.id) AS item_count,
                    SUM(CASE WHEN i.imported = 1 THEN 1 ELSE 0 END) AS imported_count,
                    SUM(CASE WHEN i.catalog_product_id IS NULL THEN 1 ELSE 0 END) AS review_count
                FROM receipts r
                LEFT JOIN receipt_items i ON i.receipt_id = r.id
                GROUP BY r.id
                ORDER BY r.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_receipt_by_hash(
        self, source_sha256: str, analysis_version: str
    ) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id FROM receipts
                WHERE source_sha256 = ? AND analysis_version = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (source_sha256, analysis_version),
            ).fetchone()
        return self.get_receipt(str(row["id"])) if row else None

    def get_receipt_by_fingerprint(
        self, receipt_fingerprint: str
    ) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id FROM receipts
                WHERE receipt_fingerprint = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (receipt_fingerprint,),
            ).fetchone()
        return self.get_receipt(str(row["id"])) if row else None

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            receipt_row = conn.execute(
                "SELECT * FROM receipts WHERE id = ?", (receipt_id,)
            ).fetchone()
            if not receipt_row:
                return None
            item_rows = conn.execute(
                """
                SELECT i.*,
                    COALESCE(v.image_url, p.image_url) AS catalog_product_image_url,
                    v.name AS catalog_variant_name,
                    v.brand AS catalog_variant_brand,
                    v.package_amount AS catalog_variant_package_amount,
                    v.package_unit AS catalog_variant_package_unit
                FROM receipt_items i
                LEFT JOIN catalog_products p ON p.id = i.catalog_product_id
                LEFT JOIN catalog_product_variants v ON v.id = i.catalog_variant_id
                WHERE i.receipt_id = ?
                ORDER BY i.position
                """,
                (receipt_id,),
            ).fetchall()
        receipt = dict(receipt_row)
        receipt["items"] = []
        for row in item_rows:
            item = dict(row)
            raw_evidence = item.pop("match_evidence_json", None)
            try:
                evidence = json.loads(str(raw_evidence)) if raw_evidence else []
            except json.JSONDecodeError:
                evidence = []
            item["match_evidence"] = evidence if isinstance(evidence, list) else []
            item["match_reason"] = item.get("match_reason") or self._legacy_match_reason(
                str(item.get("match_status") or "unresolved")
            )
            receipt["items"].append(item)
        receipt["ready_count"] = sum(
            1 for item in receipt["items"] if item["catalog_product_id"] is not None
        )
        receipt["review_count"] = len(receipt["items"]) - receipt["ready_count"]
        return receipt

    @staticmethod
    def _legacy_match_reason(match_status: str) -> str:
        return {
            "learned": "learned_store",
            "alias": "confirmed_alias",
            "barcode": "barcode",
            "exact": "exact_name",
            "manual": "manual",
            "suggested": "fuzzy_name",
        }.get(match_status, "unresolved")

    def list_receipt_items_for_reconciliation(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT i.*, r.store_name
                FROM receipt_items i
                JOIN receipts r ON r.id = i.receipt_id
                WHERE i.imported = 0 AND i.catalog_product_id IS NULL
                ORDER BY r.created_at DESC, i.position
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def apply_receipt_item_resolution(
        self, item_id: str, resolution: dict[str, Any]
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE receipt_items SET
                    catalog_product_id = ?, catalog_product_name = ?,
                    catalog_variant_id = ?, grocy_product_id = ?,
                    grocy_product_name = ?, match_status = ?, match_score = ?,
                    match_reason = ?, match_evidence_json = ?,
                    suggested_product_id = ?, suggested_product_name = ?,
                    suggested_product_score = ?, suggested_catalog_product_id = ?,
                    suggested_catalog_product_name = ?,
                    suggested_catalog_product_score = ?, updated_at = ?
                WHERE id = ? AND imported = 0 AND catalog_product_id IS NULL
                """,
                (
                    resolution.get("catalog_product_id"),
                    resolution.get("catalog_product_name"),
                    resolution.get("catalog_variant_id"),
                    resolution.get("grocy_product_id"),
                    resolution.get("grocy_product_name"),
                    resolution.get("match_status", "unresolved"),
                    resolution.get("match_score"),
                    resolution.get("match_reason", "unresolved"),
                    json.dumps(resolution.get("match_evidence") or [], ensure_ascii=False),
                    resolution.get("suggested_product_id"),
                    resolution.get("suggested_product_name"),
                    resolution.get("suggested_product_score"),
                    resolution.get("suggested_catalog_product_id"),
                    resolution.get("suggested_catalog_product_name"),
                    resolution.get("suggested_catalog_product_score"),
                    now_iso(),
                    item_id,
                ),
            )

    def update_catalog_item_mapping(
        self,
        receipt_id: str,
        item_id: str,
        product_id: str | None,
        remember: bool,
        variant_id: str | None = None,
    ) -> bool:
        timestamp = now_iso()
        with self.connect() as conn:
            item = conn.execute(
                """
                SELECT i.*, r.store_name
                FROM receipt_items i
                JOIN receipts r ON r.id = i.receipt_id
                WHERE i.id = ? AND i.receipt_id = ?
                """,
                (item_id, receipt_id),
            ).fetchone()
            if not item:
                return False
            product = None
            if product_id is not None:
                product = conn.execute(
                    "SELECT id, name FROM catalog_products WHERE id = ? AND active = 1",
                    (product_id,),
                ).fetchone()
                if not product:
                    return False
            product_name = str(product["name"]) if product else None
            if product and variant_id:
                variant = conn.execute(
                    "SELECT id FROM catalog_product_variants WHERE id = ? AND product_id = ?",
                    (variant_id, product_id),
                ).fetchone()
                variant_id = str(variant["id"]) if variant else None
            if product and not variant_id and item["barcode"]:
                variant = conn.execute(
                    """
                    SELECT v.id FROM catalog_barcodes b
                    JOIN catalog_product_variants v ON v.id = b.variant_id
                    WHERE b.barcode = ? AND v.product_id = ?
                    """,
                    (item["barcode"], product_id),
                ).fetchone()
                variant_id = str(variant["id"]) if variant else None
            if product and not variant_id:
                variants = conn.execute(
                    "SELECT id FROM catalog_product_variants WHERE product_id = ? LIMIT 2",
                    (product_id,),
                ).fetchall()
                if len(variants) == 1:
                    variant_id = str(variants[0]["id"])
            grocy_ref = None
            if product:
                grocy_ref = conn.execute(
                    """
                    SELECT external_id FROM catalog_external_refs
                    WHERE source = 'grocy' AND product_id = ? LIMIT 1
                    """,
                    (product_id,),
                ).fetchone()
            conn.execute(
                """
                UPDATE receipt_items
                SET catalog_product_id = ?, catalog_product_name = ?,
                    catalog_variant_id = ?,
                    grocy_product_id = COALESCE(?, grocy_product_id),
                    grocy_product_name = CASE WHEN ? IS NOT NULL THEN ? ELSE grocy_product_name END,
                    match_status = ?, match_score = ?, match_reason = ?,
                    match_evidence_json = ?,
                    suggested_catalog_product_id = NULL,
                    suggested_catalog_product_name = NULL,
                    suggested_catalog_product_score = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    product_id,
                    product_name,
                    variant_id,
                    int(grocy_ref["external_id"]) if grocy_ref else None,
                    grocy_ref["external_id"] if grocy_ref else None,
                    product_name,
                    "manual" if product_id is not None else "unresolved",
                    100 if product_id is not None else None,
                    "manual" if product_id is not None else "unresolved",
                    json.dumps(
                        [
                            {
                                "source": "manual",
                                "label": "Manuell zugeordnet",
                                "confidence": 1.0,
                                "automatic": False,
                            }
                        ]
                        if product_id is not None
                        else [],
                        ensure_ascii=False,
                    ),
                    timestamp,
                    item_id,
                ),
            )
            if remember and product_id is not None:
                conn.execute(
                    """
                    INSERT INTO catalog_product_mappings(
                        store_key, raw_key, product_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(store_key, raw_key) DO UPDATE SET
                        product_id = excluded.product_id,
                        updated_at = excluded.updated_at
                    """,
                    (
                        retailer_key(item["store_name"] or "*"),
                        canonical_receipt_key(item["raw_name"]),
                        product_id,
                        timestamp,
                        timestamp,
                    ),
                )
                for alias_key in {
                    canonical_receipt_key(str(item["raw_name"])),
                    canonical_receipt_key(str(item["normalized_name"] or "")),
                }:
                    if alias_key:
                        conn.execute(
                            """
                            INSERT INTO catalog_aliases(
                                alias_key, product_id, source, created_at, updated_at
                            ) VALUES (?, ?, 'confirmed', ?, ?)
                            ON CONFLICT(alias_key, product_id) DO UPDATE SET
                                source = excluded.source,
                                updated_at = excluded.updated_at
                            """,
                            (alias_key, product_id, timestamp, timestamp),
                        )
        return True

    def record_catalog_purchase(self, receipt_id: str, item_id: str) -> bool:
        timestamp = now_iso()
        with self.connect() as conn:
            item = conn.execute(
                """
                SELECT i.*, r.purchase_date
                FROM receipt_items i
                JOIN receipts r ON r.id = i.receipt_id
                WHERE i.id = ? AND i.receipt_id = ?
                """,
                (item_id, receipt_id),
            ).fetchone()
            if not item or not item["catalog_product_id"] or int(item["imported"] or 0) == 1:
                return False
            product = conn.execute(
                """
                SELECT default_location_id FROM catalog_products WHERE id = ?
                """,
                (item["catalog_product_id"],),
            ).fetchone()
            location_id = int(product["default_location_id"]) if product and product["default_location_id"] else None
            quantity_value = float(item["quantity"] or 1)
            unit_price = item["unit_price"]
            if unit_price is None and item["total_price"] is not None and quantity_value:
                unit_price = float(item["total_price"]) / quantity_value
            variant_id = item["catalog_variant_id"]
            if not variant_id and item["barcode"]:
                variant = conn.execute(
                    """
                    SELECT v.id FROM catalog_barcodes b
                    JOIN catalog_product_variants v ON v.id = b.variant_id
                    WHERE b.barcode = ? AND v.product_id = ?
                    """,
                    (item["barcode"], item["catalog_product_id"]),
                ).fetchone()
                variant_id = str(variant["id"]) if variant else None
            lot_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO stock_lots(
                    id, product_id, variant_id, location_id, quantity, best_before_date,
                    unit_price, purchased_date, receipt_item_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lot_id,
                    item["catalog_product_id"],
                    variant_id,
                    location_id,
                    quantity_value,
                    item["best_before_date"],
                    unit_price,
                    item["purchase_date"],
                    item_id,
                    timestamp,
                    timestamp,
                ),
            )
            conn.execute(
                """
                INSERT INTO stock_movements(
                    id, product_id, variant_id, lot_id, location_id, movement_type,
                    quantity_delta, source, reference_id, created_at
                ) VALUES (?, ?, ?, ?, ?, 'purchase', ?, 'receipt', ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    item["catalog_product_id"],
                    variant_id,
                    lot_id,
                    location_id,
                    quantity_value,
                    receipt_id,
                    timestamp,
                ),
            )
            conn.execute(
                """
                UPDATE receipt_items
                SET imported = 1, import_error = NULL, updated_at = ? WHERE id = ?
                """,
                (timestamp, item_id),
            )
        return True

    def mark_grocy_exported(self, item_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE receipt_items SET grocy_exported = 1, updated_at = ? WHERE id = ?",
                (now_iso(), item_id),
            )

    def update_item_mapping(
        self,
        receipt_id: str,
        item_id: str,
        product_id: int | None,
        product_name: str | None,
        remember: bool,
    ) -> bool:
        timestamp = now_iso()
        with self.connect() as conn:
            item = conn.execute(
                """
                SELECT i.*, r.store_name
                FROM receipt_items i
                JOIN receipts r ON r.id = i.receipt_id
                WHERE i.id = ? AND i.receipt_id = ?
                """,
                (item_id, receipt_id),
            ).fetchone()
            if not item:
                return False
            conn.execute(
                """
                UPDATE receipt_items
                SET grocy_product_id = ?, grocy_product_name = ?,
                    match_status = ?, match_score = ?,
                    suggested_product_id = NULL, suggested_product_name = NULL,
                    suggested_product_score = NULL, updated_at = ?
                WHERE id = ?
                """,
                (
                    product_id,
                    product_name,
                    "manual" if product_id is not None else "unresolved",
                    100 if product_id is not None else None,
                    timestamp,
                    item_id,
                ),
            )
            if remember and product_id is not None and product_name:
                conn.execute(
                    """
                    INSERT INTO product_mappings(
                        store_key, raw_key, grocy_product_id,
                        grocy_product_name, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(store_key, raw_key) DO UPDATE SET
                        grocy_product_id = excluded.grocy_product_id,
                        grocy_product_name = excluded.grocy_product_name,
                        updated_at = excluded.updated_at
                    """,
                    (
                        retailer_key(item["store_name"] or "*"),
                        canonical_receipt_key(item["raw_name"]),
                        product_id,
                        product_name,
                        timestamp,
                        timestamp,
                    ),
                )
                self._remember_aliases(
                    conn,
                    str(item["raw_name"]),
                    str(item["normalized_name"] or ""),
                    product_id,
                    product_name,
                    "confirmed",
                )
        return True

    def update_receipt_store_id(self, receipt_id: str, store_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE receipts SET grocy_store_id = ?, updated_at = ? WHERE id = ?",
                (store_id, now_iso(), receipt_id),
            )

    def get_mapping(self, store_name: str | None, raw_name: str) -> dict[str, Any] | None:
        store_key = retailer_key(store_name or "*")
        raw_key = canonical_receipt_key(raw_name)
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM product_mappings
                WHERE raw_key = ? AND store_key IN (?, '*')
                ORDER BY CASE WHEN store_key = ? THEN 0 ELSE 1 END
                LIMIT 1
                """,
                (raw_key, store_key, store_key),
            ).fetchone()
        return dict(row) if row else None

    def get_alias(
        self, raw_name: str, normalized_name: str | None
    ) -> dict[str, Any] | None:
        keys = {
            canonical_receipt_key(raw_name),
            canonical_receipt_key(normalized_name or ""),
        }
        keys.discard("")
        if not keys:
            return None
        key_values = sorted(keys)
        key_values.extend([""] * (2 - len(key_values)))
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT grocy_product_id, grocy_product_name
                FROM product_aliases
                WHERE alias_key IN (?, ?)
                GROUP BY grocy_product_id, grocy_product_name
                """,
                tuple(key_values),
            ).fetchall()
        products = {int(row["grocy_product_id"]): dict(row) for row in rows}
        return next(iter(products.values())) if len(products) == 1 else None

    def _remember_aliases(
        self,
        conn: sqlite3.Connection,
        raw_name: str,
        normalized_name: str,
        product_id: int,
        product_name: str,
        source: str,
    ) -> None:
        timestamp = now_iso()
        keys = {
            canonical_receipt_key(raw_name),
            canonical_receipt_key(normalized_name),
        }
        for alias_key in keys:
            if not alias_key:
                continue
            conn.execute(
                """
                INSERT INTO product_aliases(
                    alias_key, grocy_product_id, grocy_product_name,
                    source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(alias_key, grocy_product_id) DO UPDATE SET
                    grocy_product_name = excluded.grocy_product_name,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                (alias_key, product_id, product_name, source, timestamp, timestamp),
            )

    def mark_item_imported(self, item_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE receipt_items
                SET imported = 1, import_error = NULL, updated_at = ?
                WHERE id = ?
                """,
                (now_iso(), item_id),
            )

    def mark_item_failed(self, item_id: str, error: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE receipt_items
                SET import_error = ?, updated_at = ?
                WHERE id = ?
                """,
                (error[:500], now_iso(), item_id),
            )

    def save_import_run(
        self,
        run_id: str,
        receipt_id: str,
        requested_count: int,
        imported_count: int,
        failed_count: int,
        details: list[dict[str, Any]],
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO import_runs(
                    id, receipt_id, requested_count, imported_count,
                    failed_count, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    receipt_id,
                    requested_count,
                    imported_count,
                    failed_count,
                    json.dumps(details, ensure_ascii=False),
                    now_iso(),
                ),
            )
            status = "imported" if failed_count == 0 else "partial"
            conn.execute(
                "UPDATE receipts SET status = ?, updated_at = ? WHERE id = ?",
                (status, now_iso(), receipt_id),
            )


def normalize_key(value: str) -> str:
    replacements = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
    normalized = value.strip().lower().translate(replacements)
    return " ".join("".join(ch if ch.isalnum() else " " for ch in normalized).split())


def canonical_receipt_key(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = re.sub(r"\s+\d{1,5}[,.]\d{2}\s*(?:EUR|€)?\s*[A-Z*]?\s*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+\d+(?:[,.]\d+)?\s*(?:STK\.?|STÜCK|X)\b.*$", "", cleaned, flags=re.I)
    return normalize_key(cleaned)


def retailer_key(value: str) -> str:
    key = normalize_key(value)
    known = {
        "rewe": "rewe",
        "dm": "dm",
        "drogerie markt": "dm",
        "aldi": "aldi",
        "lidl": "lidl",
        "edeka": "edeka",
        "kaufland": "kaufland",
        "rossmann": "rossmann",
        "netto": "netto",
        "penny": "penny",
    }
    for needle, result in known.items():
        if needle in key.split() or needle in key:
            return result
    return key or "*"
