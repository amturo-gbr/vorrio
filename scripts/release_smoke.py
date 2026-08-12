#!/usr/bin/env python3
"""Run a deterministic launch journey against an isolated Vorrio database."""

from __future__ import annotations

import io
import json
import os
import tempfile
import uuid
import zipfile
from pathlib import Path


test_root = Path(tempfile.mkdtemp(prefix="vorrio-release-smoke-"))
os.environ["DATA_DIR"] = str(test_root)
os.environ["APP_SECRET_KEY"] = "release-smoke-secret-key-that-is-long-enough"
os.environ["APP_PASSWORD"] = ""
os.environ["SESSION_HTTPS_ONLY"] = "false"
os.environ["DEPLOYMENT_PROFILE"] = "lan"
os.environ["TRUSTED_HOSTS"] = "testserver,localhost"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app, database  # noqa: E402


def require(response, expected: int = 200):
    if response.status_code != expected:
        raise AssertionError(f"{response.request.method} {response.request.url}: {response.status_code} {response.text}")
    return response.json() if response.content else None


with TestClient(app) as client:
    owner = require(client.post(
        "/api/v1/auth/setup",
        json={"password": "sicheres-smoke-passwort", "display_name": "Release-Test"},
    ))
    assert owner["user"]["role"] == "owner"

    product = require(client.post(
        "/api/v1/catalog/products",
        json={
            "name": "Haferdrink Launch-Test",
            "new_location_name": "Vorratskammer",
            "new_quantity_unit_name": "Packung",
            "new_product_group_name": "Getränke",
            "minimum_stock_quantity": 2,
            "shopping_target_quantity": 4,
            "barcode": "4006381333931",
        },
    ))
    product_id = product["id"]
    variant_id = product["variants"][0]["id"]

    receipt_id = str(uuid.uuid4())
    database.create_receipt(
        {
            "id": receipt_id,
            "store_name": "Testmarkt",
            "purchase_date": "2026-08-12",
            "currency": "EUR",
            "total": 2.49,
            "status": "review",
            "analysis_version": app.version,
        },
        [{
            "id": str(uuid.uuid4()),
            "raw_name": "HAFERDRINK BARISTA",
            "normalized_name": "Haferdrink Barista",
            "quantity": 1,
            "unit_price": 2.49,
            "total_price": 2.49,
            "catalog_product_id": product_id,
            "catalog_product_name": product["name"],
            "catalog_variant_id": variant_id,
            "match_status": "confirmed",
            "match_reason": "synthetic release journey",
        }],
    )
    imported = require(client.post(f"/api/v1/receipts/{receipt_id}/import", json={"item_ids": None}))
    assert imported["imported"] == 1 and imported["failed"] == 0

    budget = require(client.put(
        "/api/v1/insights/budget/settings",
        json={"monthly_limit": 400, "warning_percent": 80},
    ))
    assert budget["configured"] is True
    overview = require(client.get("/api/v1/insights/budget?months=2"))
    assert overview["settings"]["monthly_limit"] == 400

    lookup = require(client.get("/api/v1/catalog/barcodes/4006381333931/lookup"))
    assert lookup["found"] is True and lookup["product"]["id"] == product_id

    operations = require(client.get("/api/v1/operations/overview"))
    assert operations["database_integrity"] == "ok"
    assert operations["counts"]["products"] == 1
    assert operations["counts"]["stock_lots"] == 1

    exported = client.get("/api/v1/privacy/export?include_receipt_files=false")
    if exported.status_code != 200:
        raise AssertionError(f"portable export failed: {exported.status_code} {exported.text}")
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["format"] == "vorrio-portable-export"
        assert manifest["counts"]["products"] == 1
        assert manifest["counts"]["stock_lots"] == 1
        assert manifest["receipt_files_included"] == 0
        joined = b"".join(archive.read(name) for name in archive.namelist())
        assert b"release-smoke-secret-key" not in joined

print("Vorrio launch smoke passed: setup -> catalog -> receipt -> stock -> budget -> export -> operations")
