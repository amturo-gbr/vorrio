from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz

from ..database import Database, normalize_key, retailer_key
from .grocy import GrocyClient


async def match_items(
    *,
    database: Database,
    grocy: GrocyClient | None,
    store_name: str | None,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grocy_products = await grocy.products() if grocy else []
    catalog_products = database.list_catalog_products(limit=10000)
    catalog_names = [
        (product, normalize_key(str(product.get("name", ""))))
        for product in catalog_products
    ]
    grocy_names = [
        (product, normalize_key(str(product.get("name", ""))))
        for product in grocy_products
    ]

    for item in items:
        _prepare_item(item)
        if _resolve_local_item(
            database=database,
            store_name=store_name,
            item=item,
            catalog_products=catalog_products,
            catalog_names=catalog_names,
        ):
            continue

        if grocy and item["barcode"]:
            barcode_match = await grocy.product_by_barcode(str(item["barcode"]))
            product = (barcode_match or {}).get("product") if barcode_match else None
            if isinstance(product, dict) and product.get("id"):
                catalog_product = database.upsert_grocy_product(
                    int(product["id"]), str(product.get("name", item["raw_name"]))
                )
                _set_catalog_match(
                    item,
                    catalog_product,
                    status="barcode",
                    reason="barcode",
                    label="Barcode stimmt exakt",
                )
                item["grocy_product_id"] = int(product["id"])
                item["grocy_product_name"] = str(product.get("name", item["raw_name"]))
                continue

        lookup = normalize_key(str(item["normalized_name"]))
        exact = next((product for product, name in grocy_names if name == lookup), None)
        if exact:
            catalog_product = database.upsert_grocy_product(
                int(exact["id"]), str(exact["name"])
            )
            _set_catalog_match(
                item,
                catalog_product,
                status="exact",
                reason="exact_name",
                label="Produktname stimmt exakt",
            )
            item["grocy_product_id"] = int(exact["id"])
            item["grocy_product_name"] = str(exact["name"])
            continue

        scored = sorted(
            (
                (fuzz.WRatio(lookup, product_name), product)
                for product, product_name in grocy_names
                if product_name
            ),
            key=lambda value: value[0],
            reverse=True,
        )
        if scored and scored[0][0] >= 90:
            score, product = scored[0]
            catalog_product = database.upsert_grocy_product(
                int(product["id"]), str(product["name"])
            )
            _set_suggestion(item, catalog_product, float(score))
            item["suggested_product_id"] = int(product["id"])
            item["suggested_product_name"] = str(product["name"])
            item["suggested_product_score"] = round(float(score), 1)
    return items


def reconcile_unresolved_items(database: Database) -> dict[str, int]:
    catalog_products = database.list_catalog_products(limit=10000)
    catalog_names = [
        (product, normalize_key(str(product.get("name", ""))))
        for product in catalog_products
    ]
    rows = database.list_receipt_items_for_reconciliation()
    resolved = 0
    suggested = 0
    for row in rows:
        item = dict(row)
        _prepare_item(item)
        _resolve_local_item(
            database=database,
            store_name=item.get("store_name"),
            item=item,
            catalog_products=catalog_products,
            catalog_names=catalog_names,
        )
        database.apply_receipt_item_resolution(str(item["id"]), item)
        if item.get("catalog_product_id"):
            resolved += 1
        elif item.get("suggested_catalog_product_id"):
            suggested += 1
    return {"scanned": len(rows), "resolved": resolved, "suggested": suggested}


def _resolve_local_item(
    *,
    database: Database,
    store_name: str | None,
    item: dict[str, Any],
    catalog_products: list[dict[str, Any]],
    catalog_names: list[tuple[dict[str, Any], str]],
) -> bool:
    if item.get("barcode"):
        barcode_product = database.catalog_product_by_barcode(str(item["barcode"]))
        if barcode_product:
            _set_catalog_match(
                item,
                barcode_product,
                status="barcode",
                reason="barcode",
                label="Barcode stimmt exakt",
            )
            item["catalog_variant_id"] = barcode_product.get("variant_id")
            return True

    mapping = database.get_catalog_mapping(store_name, str(item["raw_name"]))
    if mapping:
        product = _catalog_product(catalog_products, str(mapping["product_id"])) or mapping
        store = _store_label(store_name)
        _set_catalog_match(
            item,
            product,
            status="learned",
            reason="learned_store",
            label=f"Bei {store} gelernt" if store else "Für dieses Geschäft gelernt",
        )
        return True

    alias = database.get_catalog_alias(
        str(item["raw_name"]), str(item.get("normalized_name") or "")
    )
    if alias:
        product = _catalog_product(catalog_products, str(alias["product_id"])) or alias
        _set_catalog_match(
            item,
            product,
            status="alias",
            reason="confirmed_alias",
            label="Schon einmal bestätigt",
        )
        return True

    lookup = normalize_key(str(item["normalized_name"]))
    catalog_exact = next((product for product, name in catalog_names if name == lookup), None)
    if catalog_exact:
        _set_catalog_match(
            item,
            catalog_exact,
            status="exact",
            reason="exact_name",
            label="Produktname stimmt exakt",
        )
        return True

    catalog_scored = sorted(
        (
            (fuzz.WRatio(lookup, product_name), product)
            for product, product_name in catalog_names
            if product_name
        ),
        key=lambda value: value[0],
        reverse=True,
    )
    if catalog_scored and catalog_scored[0][0] >= 90:
        score, product = catalog_scored[0]
        _set_suggestion(item, product, float(score))
    return False


def _prepare_item(item: dict[str, Any]) -> None:
    raw_name = str(item.get("raw_name") or item.get("normalized_name") or "Unbekannt")
    normalized_name = str(item.get("normalized_name") or raw_name)
    item["raw_name"] = raw_name
    item["normalized_name"] = normalized_name
    item["quantity"] = _number(item.get("quantity"), 1.0)
    if not item["quantity"] or item["quantity"] <= 0:
        item["quantity"] = 1.0
    item["unit_price"] = _number(item.get("unit_price"), None)
    item["total_price"] = _number(item.get("total_price"), None)
    item["barcode"] = item.get("barcode") or None
    item["brand"] = item.get("brand") or None
    best_before = str(item.get("best_before_date") or "")
    item["best_before_date"] = (
        best_before if re.fullmatch(r"\d{4}-\d{2}-\d{2}", best_before) else None
    )
    item["suggested_location"] = item.get("suggested_location") or None
    item["suggested_unit"] = item.get("suggested_unit") or None
    item["suggested_product_group"] = item.get("suggested_product_group") or None
    item["suggested_best_before_days"] = _integer(
        item.get("suggested_best_before_days"), None
    )
    if item["suggested_best_before_days"] is not None:
        item["suggested_best_before_days"] = max(
            0, min(3650, item["suggested_best_before_days"])
        )
    item["suggestion_confidence"] = _number(item.get("suggestion_confidence"), None)
    if item["suggestion_confidence"] is not None:
        item["suggestion_confidence"] = max(
            0.0, min(1.0, item["suggestion_confidence"])
        )
    for key in (
        "grocy_product_id",
        "grocy_product_name",
        "catalog_product_id",
        "catalog_product_name",
        "catalog_variant_id",
        "suggested_product_id",
        "suggested_product_name",
        "suggested_product_score",
        "suggested_catalog_product_id",
        "suggested_catalog_product_name",
        "suggested_catalog_product_score",
    ):
        item[key] = None
    item["match_status"] = "unresolved"
    item["match_score"] = None
    item["match_reason"] = "unresolved"
    item["match_evidence"] = []


def _set_catalog_match(
    item: dict[str, Any],
    product: dict[str, Any],
    *,
    status: str,
    reason: str,
    label: str,
) -> None:
    product_id = product.get("id") or product.get("product_id")
    product_name = product.get("name") or product.get("product_name")
    item.update(
        {
            "catalog_product_id": product_id,
            "catalog_product_name": product_name,
            "catalog_variant_id": product.get("variant_id"),
            "match_status": status,
            "match_score": 100,
            "match_reason": reason,
            "match_evidence": [
                {
                    "source": reason,
                    "label": label,
                    "confidence": 1.0,
                    "automatic": True,
                }
            ],
        }
    )
    if product.get("grocy_product_id"):
        item["grocy_product_id"] = product["grocy_product_id"]
        item["grocy_product_name"] = product_name


def _set_suggestion(
    item: dict[str, Any], product: dict[str, Any], score: float
) -> None:
    rounded = round(score, 1)
    item.update(
        {
            "suggested_catalog_product_id": product["id"],
            "suggested_catalog_product_name": product["name"],
            "suggested_catalog_product_score": rounded,
            "match_status": "suggested",
            "match_reason": "fuzzy_name",
            "match_evidence": [
                {
                    "source": "fuzzy_name",
                    "label": f"{round(rounded):d} % ähnlich – bitte prüfen",
                    "confidence": rounded / 100,
                    "automatic": False,
                }
            ],
        }
    )


def _catalog_product(
    products: list[dict[str, Any]], product_id: str
) -> dict[str, Any] | None:
    return next((product for product in products if str(product.get("id")) == product_id), None)


def _store_label(store_name: str | None) -> str:
    key = retailer_key(store_name or "")
    return {"rewe": "REWE", "dm": "dm", "aldi": "ALDI", "lidl": "Lidl"}.get(
        key, str(store_name or "").strip()
    )


def _number(value: Any, fallback: float | None) -> float | None:
    if value is None or value == "":
        return fallback
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return fallback


def _integer(value: Any, fallback: int | None) -> int | None:
    number = _number(value, None)
    return int(round(number)) if number is not None else fallback
