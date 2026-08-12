from __future__ import annotations

from typing import Any

import httpx


class ProductDataError(RuntimeError):
    pass


USER_AGENT = "Vorrio/0.8.0 (self-hosted open-source client)"


async def lookup_open_facts(barcode: str) -> dict[str, Any] | None:
    code = "".join(character for character in barcode if character.isdigit())
    if len(code) < 4 or len(code) > 18:
        raise ProductDataError("Der Barcode ist ungültig")

    fields = ",".join(
        (
            "code",
            "product_name",
            "product_name_de",
            "brands",
            "quantity",
            "image_front_url",
            "categories",
            "product_type",
        )
    )
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            response = await client.get(
                f"https://world.openfoodfacts.org/api/v3/product/{code}",
                params={"product_type": "all", "fields": fields, "lc": "de", "cc": "de"},
                headers={
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
            )
    except httpx.HTTPError as exc:
        raise ProductDataError(f"Open Facts ist nicht erreichbar: {exc}") from exc
    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise ProductDataError(f"Open Facts antwortet mit HTTP {response.status_code}")
    payload = response.json()
    product = payload.get("product") if isinstance(payload, dict) else None
    if not isinstance(product, dict):
        return None
    return {
        "barcode": str(product.get("code") or code),
        "name": str(
            product.get("product_name_de") or product.get("product_name") or ""
        ).strip(),
        "brand": str(product.get("brands") or "").strip() or None,
        "quantity": str(product.get("quantity") or "").strip() or None,
        "image_url": str(product.get("image_front_url") or "").strip() or None,
        "categories": str(product.get("categories") or "").strip() or None,
        "product_type": str(product.get("product_type") or "").strip() or None,
        "source": "Open Facts",
        "source_url": f"https://world.openfoodfacts.org/product/{code}",
        "database_license": "ODbL-1.0",
        "image_license": "CC-BY-SA",
        "attribution": "Open Food Facts contributors",
    }


async def search_open_facts(query: str, *, limit: int = 6) -> list[dict[str, Any]]:
    search_query = " ".join(query.split()).strip()
    if len(search_query) < 2:
        return []
    fields = ",".join(
        (
            "code",
            "product_name",
            "product_name_de",
            "brands",
            "quantity",
            "image_front_url",
            "categories",
            "product_type",
            "stores",
            "stores_tags",
            "countries_tags",
        )
    )
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(
                "https://search.openfoodfacts.org/search",
                params={
                    "q": search_query,
                    "page_size": max(1, min(limit, 10)),
                    "langs": "de,en",
                    "boost_phrase": "true",
                    "fields": fields,
                },
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            )
    except httpx.HTTPError as exc:
        raise ProductDataError(f"Open-Facts-Suche ist nicht erreichbar: {exc}") from exc
    if response.status_code == 429:
        raise ProductDataError(
            "Open Facts begrenzt die Suche gerade. Bitte den Vorschlag später erneut öffnen."
        )
    if response.status_code >= 400:
        raise ProductDataError(
            f"Open-Facts-Suche antwortet mit HTTP {response.status_code}"
        )
    payload = response.json()
    hits = payload.get("hits") if isinstance(payload, dict) else None
    if not isinstance(hits, list):
        return []
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        code = str(hit.get("code") or "").strip()
        name = str(hit.get("product_name_de") or hit.get("product_name") or "").strip()
        if not code or not name or code in seen:
            continue
        seen.add(code)
        brands = _string_list(hit.get("brands"))
        stores = _string_list(hit.get("stores")) + _string_list(hit.get("stores_tags"))
        candidates.append(
            {
                "barcode": code,
                "name": name,
                "brand": brands[0] if brands else None,
                "brands": brands,
                "quantity": str(hit.get("quantity") or "").strip() or None,
                "image_url": str(hit.get("image_front_url") or "").strip() or None,
                "categories": str(hit.get("categories") or "").strip() or None,
                "product_type": str(hit.get("product_type") or "").strip() or None,
                "stores": sorted(set(stores)),
                "countries": _string_list(hit.get("countries_tags")),
                "source": "Open Facts",
                "source_url": f"https://world.openfoodfacts.org/product/{code}",
                "database_license": "ODbL-1.0",
                "image_license": "CC-BY-SA",
                "attribution": "Open Food Facts contributors",
            }
        )
    return candidates


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []
