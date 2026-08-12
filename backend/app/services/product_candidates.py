from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from rapidfuzz import fuzz

from ..database import Database, normalize_key, retailer_key
from .product_data import ProductDataError, search_open_facts
from .providers import ProviderError, rank_product_candidates


CACHE_SOURCE = "product_candidate_search_v1"


async def find_product_candidates(
    *,
    database: Database,
    provider_settings: dict[str, Any],
    receipt: dict[str, Any],
    item: dict[str, Any],
    limit: int = 3,
) -> dict[str, Any]:
    query = " ".join(
        str(item.get("normalized_name") or item.get("raw_name") or "").split()
    ).strip()
    store_name = str(receipt.get("store_name") or receipt.get("retailer") or "").strip()
    unit_price = _unit_price(item)
    cache_key = _cache_key(
        query=query,
        store_name=store_name,
        unit_price=unit_price,
        provider_type=str(provider_settings.get("type") or ""),
        provider_model=str(provider_settings.get("model") or ""),
    )
    cached = database.get_external_product(CACHE_SOURCE, cache_key, max_age_days=30)
    if cached and isinstance(cached.get("candidates"), list):
        local_products = database.list_catalog_products(limit=10000)
        for candidate in cached["candidates"]:
            if not isinstance(candidate, dict):
                continue
            local = _local_product(database, local_products, candidate)
            candidate["local_product_id"] = str(local["id"]) if local else None
            candidate["local_product_name"] = str(local["name"]) if local else None
        return {**cached, "cached": True}

    warnings: list[str] = []
    try:
        raw_candidates = await search_open_facts(query, limit=8)
    except ProductDataError as exc:
        raw_candidates = []
        warnings.append(str(exc))

    local_products = database.list_catalog_products(limit=10000)
    ranked = [
        _score_candidate(
            database=database,
            local_products=local_products,
            query=query,
            item=item,
            store_name=store_name,
            candidate=candidate,
        )
        for candidate in raw_candidates
    ]
    ranked = [candidate for candidate in ranked if candidate["score"] >= 35]
    ranked.sort(key=lambda candidate: candidate["score"], reverse=True)

    ai_ranking: dict[str, dict[str, Any]] = {}
    if ranked and provider_settings.get("model"):
        try:
            ai_ranking = await rank_product_candidates(
                provider_settings,
                receipt_context={
                    "line": query,
                    "brand": item.get("brand"),
                    "store": store_name or None,
                    "retailer": receipt.get("retailer"),
                    "quantity": item.get("quantity"),
                    "receipt_unit_price": unit_price,
                    "currency": receipt.get("currency") or "EUR",
                },
                candidates=ranked,
            )
        except ProviderError as exc:
            warnings.append(f"KI-Sortierung nicht verfügbar: {exc}")

    for candidate in ranked:
        ai = ai_ranking.get(str(candidate["external_id"]))
        if ai:
            candidate["ai_confidence"] = round(float(ai["confidence"]) * 100, 1)
            candidate["ai_reason"] = ai.get("reason") or None
            candidate["score"] = round(
                candidate["score"] * 0.68 + float(ai["confidence"]) * 100 * 0.32,
                1,
            )
            candidate["evidence"].insert(
                0,
                {
                    "source": "ai_ranking",
                    "label": candidate["ai_reason"] or "Vom gewählten KI-Modell priorisiert",
                },
            )
        database.put_external_product(
            "open_facts",
            str(candidate["external_id"]),
            _candidate_cache_payload(candidate),
            source_url=candidate.get("source_url"),
            license_name=candidate.get("database_license"),
            attribution=candidate.get("attribution"),
        )
    ranked.sort(key=lambda candidate: candidate["score"], reverse=True)
    selected = _select_candidates(ranked, limit)
    result = {
        "query": query,
        "store_name": store_name or None,
        "receipt_unit_price": unit_price,
        "currency": receipt.get("currency") or "EUR",
        "source": "open_facts",
        "cached": False,
        "ai_ranked": bool(ai_ranking),
        "candidates": selected,
        "warnings": warnings,
    }
    if not warnings or selected:
        database.put_external_product(
            CACHE_SOURCE,
            cache_key,
            result,
            source_url="https://search.openfoodfacts.org/",
            license_name="ODbL-1.0",
            attribution="Open Food Facts contributors",
        )
    return result


def _select_candidates(
    ranked: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    selection_limit = max(1, min(limit, 5))
    selected = list(ranked[:selection_limit])
    image_candidates = [
        candidate for candidate in ranked if candidate.get("image_url")
    ]
    desired_images = min(2, selection_limit, len(image_candidates))
    selected_ids = {str(candidate["external_id"]) for candidate in selected}
    additions = [
        candidate
        for candidate in image_candidates
        if str(candidate["external_id"]) not in selected_ids
    ]
    while (
        sum(bool(candidate.get("image_url")) for candidate in selected)
        < desired_images
        and additions
    ):
        replace_at = next(
            (
                index
                for index in range(len(selected) - 1, -1, -1)
                if not selected[index].get("image_url")
            ),
            None,
        )
        if replace_at is None:
            break
        selected[replace_at] = additions.pop(0)
    return sorted(selected, key=lambda candidate: candidate["score"], reverse=True)


def _score_candidate(
    *,
    database: Database,
    local_products: list[dict[str, Any]],
    query: str,
    item: dict[str, Any],
    store_name: str,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    candidate_name = str(candidate.get("name") or "")
    brand = str(candidate.get("brand") or "")
    name_score = float(
        fuzz.WRatio(normalize_key(query), normalize_key(f"{candidate_name} {brand}"))
    )
    evidence: list[dict[str, str]] = [
        {"source": "name", "label": f"Produktname {round(name_score):d} % ähnlich"}
    ]
    score = name_score * 0.72

    item_brand = normalize_key(str(item.get("brand") or ""))
    candidate_brand = normalize_key(brand)
    if item_brand and candidate_brand:
        brand_score = float(fuzz.WRatio(item_brand, candidate_brand))
        score += brand_score * 0.1
        if brand_score >= 85:
            evidence.append({"source": "brand", "label": "Marke passt"})

    store_match = _store_matches(store_name, candidate.get("stores") or [])
    if store_match:
        score += 11
        evidence.append(
            {"source": "store", "label": f"Bei {_store_label(store_name)} gelistet"}
        )

    quantity_match = _quantity_matches(query, str(candidate.get("quantity") or ""))
    if quantity_match:
        score += 7
        evidence.append({"source": "quantity", "label": "Packungsmenge passt"})

    countries = [normalize_key(str(value)) for value in candidate.get("countries") or []]
    if any(value in {"en germany", "de deutschland", "germany", "deutschland"} for value in countries):
        score += 3

    barcode = str(candidate.get("barcode") or "")
    local = _local_product(database, local_products, candidate)
    return {
        "external_id": barcode,
        "barcode": barcode,
        "name": candidate_name,
        "brand": candidate.get("brand"),
        "quantity": candidate.get("quantity"),
        "image_url": candidate.get("image_url"),
        "stores": candidate.get("stores") or [],
        "source": "open_facts",
        "source_label": "Open Facts",
        "source_url": candidate.get("source_url"),
        "database_license": candidate.get("database_license"),
        "image_license": candidate.get("image_license"),
        "attribution": candidate.get("attribution"),
        "score": round(min(score, 99.0), 1),
        "ai_confidence": None,
        "ai_reason": None,
        "store_match": store_match,
        "local_product_id": str(local["id"]) if local else None,
        "local_product_name": str(local["name"]) if local else None,
        "evidence": evidence,
    }


def _candidate_cache_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        key: candidate.get(key)
        for key in (
            "barcode",
            "name",
            "brand",
            "quantity",
            "image_url",
            "stores",
            "source_label",
            "source_url",
            "database_license",
            "image_license",
            "attribution",
        )
    }


def _local_product(
    database: Database,
    local_products: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> dict[str, Any] | None:
    barcode = str(candidate.get("barcode") or candidate.get("external_id") or "")
    local = database.catalog_product_by_barcode(barcode) if barcode else None
    if local:
        return local
    candidate_key = normalize_key(str(candidate.get("name") or ""))
    return next(
        (
            product
            for product in local_products
            if normalize_key(str(product.get("name") or "")) == candidate_key
        ),
        None,
    )


def _cache_key(**values: Any) -> str:
    raw = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _unit_price(item: dict[str, Any]) -> float | None:
    value = item.get("unit_price")
    quantity = float(item.get("quantity") or 1)
    if value is None and item.get("total_price") is not None and quantity > 0:
        value = float(item["total_price"]) / quantity
    return round(float(value), 2) if value is not None else None


def _quantity_matches(query: str, candidate_quantity: str) -> bool:
    if not candidate_quantity:
        return False
    units = r"(?:ml|cl|l|g|kg|stk|stück)"
    query_values = {
        re.sub(r"\s+", "", value.lower().replace(",", "."))
        for value in re.findall(rf"\b\d+(?:[,.]\d+)?\s*{units}\b", query, re.IGNORECASE)
    }
    candidate_values = {
        re.sub(r"\s+", "", value.lower().replace(",", "."))
        for value in re.findall(
            rf"\b\d+(?:[,.]\d+)?\s*{units}\b", candidate_quantity, re.IGNORECASE
        )
    }
    return bool(query_values & candidate_values)


def _store_matches(store_name: str, stores: list[Any]) -> bool:
    expected = retailer_key(store_name)
    if not expected:
        return False
    return any(expected in retailer_key(str(store)) for store in stores)


def _store_label(store_name: str) -> str:
    key = retailer_key(store_name)
    return {"rewe": "REWE", "aldi": "ALDI", "lidl": "Lidl", "dm": "dm"}.get(
        key, store_name.strip() or "diesem Geschäft"
    )
