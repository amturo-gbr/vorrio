from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import quote

import httpx2 as httpx

from .outbound_urls import normalize_connector_url


class GrocyError(RuntimeError):
    pass


class GrocyClient:
    def __init__(self, url: str, api_key: str, timeout: float = 20) -> None:
        self.base_url = normalize_connector_url(url) + "/api"
        self.headers = {"GROCY-API-KEY": api_key, "Accept": "application/json"}
        self.timeout = timeout

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}/{path.lstrip('/')}",
                    headers=self.headers,
                    **kwargs,
                )
        except httpx.HTTPError as exc:
            raise GrocyError(f"Grocy ist nicht erreichbar: {exc}") from exc
        if response.status_code >= 400:
            message = response.text.strip()[:500] or f"HTTP {response.status_code}"
            raise GrocyError(f"Grocy: {message}")
        if not response.content:
            return None
        return response.json()

    async def test(self) -> dict[str, Any]:
        result = await self._request("GET", "system/info")
        return result if isinstance(result, dict) else {"connected": True}

    async def products(self) -> list[dict[str, Any]]:
        result = await self._request("GET", "objects/products")
        return result if isinstance(result, list) else []

    async def stock(self) -> list[dict[str, Any]]:
        result = await self._request("GET", "stock")
        return result if isinstance(result, list) else []

    async def stores(self) -> list[dict[str, Any]]:
        result = await self._request("GET", "objects/shopping_locations")
        return result if isinstance(result, list) else []

    async def master_data(self) -> dict[str, list[dict[str, Any]]]:
        entities = {
            "locations": "locations",
            "quantity_units": "quantity_units",
            "product_groups": "product_groups",
        }
        result: dict[str, list[dict[str, Any]]] = {}
        for key, entity in entities.items():
            rows = await self._request("GET", f"objects/{entity}")
            result[key] = rows if isinstance(rows, list) else []
        return result

    async def create_product(
        self,
        *,
        name: str,
        location_id: int,
        quantity_unit_id: int,
        product_group_id: int | None,
        default_best_before_days: int,
    ) -> int:
        body: dict[str, Any] = {
            "name": name.strip(),
            "location_id": location_id,
            "qu_id_purchase": quantity_unit_id,
            "qu_id_stock": quantity_unit_id,
            "min_stock_amount": 0,
            "default_best_before_days": default_best_before_days,
        }
        if product_group_id is not None:
            body["product_group_id"] = product_group_id
        result = await self._request("POST", "objects/products", json=body)
        try:
            return int(result["created_object_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GrocyError("Grocy lieferte nach der Produktanlage keine Produkt-ID") from exc

    async def _ensure_master_object(
        self,
        *,
        entity: str,
        name: str,
        create_body: dict[str, Any],
    ) -> int:
        clean_name = name.strip()
        normalized = clean_name.casefold()
        rows = await self._request("GET", f"objects/{entity}")
        rows = rows if isinstance(rows, list) else []
        existing = next(
            (
                row
                for row in rows
                if str(row.get("name", "")).strip().casefold() == normalized
            ),
            None,
        )
        if existing:
            return int(existing["id"])
        result = await self._request(
            "POST",
            f"objects/{entity}",
            json={"name": clean_name, "active": 1, **create_body},
        )
        try:
            return int(result["created_object_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GrocyError(
                f"Grocy lieferte nach der Anlage von {clean_name} keine ID"
            ) from exc

    async def ensure_location(self, name: str, *, is_freezer: bool = False) -> int:
        return await self._ensure_master_object(
            entity="locations",
            name=name,
            create_body={"description": "", "is_freezer": 1 if is_freezer else 0},
        )

    async def ensure_quantity_unit(self, name: str) -> int:
        return await self._ensure_master_object(
            entity="quantity_units",
            name=name,
            create_body={"name_plural": name.strip(), "description": ""},
        )

    async def ensure_product_group(self, name: str) -> int:
        return await self._ensure_master_object(
            entity="product_groups",
            name=name,
            create_body={"description": ""},
        )

    async def ensure_store(self, name: str) -> int:
        normalized = name.strip().casefold()
        existing = next(
            (
                store
                for store in await self.stores()
                if str(store.get("name", "")).strip().casefold() == normalized
            ),
            None,
        )
        if existing:
            return int(existing["id"])
        result = await self._request(
            "POST",
            "objects/shopping_locations",
            json={"name": name.strip(), "active": 1},
        )
        try:
            return int(result["created_object_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GrocyError("Grocy lieferte nach der Geschäftsanlage keine ID") from exc

    async def product_by_barcode(self, barcode: str) -> dict[str, Any] | None:
        try:
            result = await self._request(
                "GET", f"stock/products/by-barcode/{quote(barcode, safe='')}"
            )
        except GrocyError:
            return None
        return result if isinstance(result, dict) else None

    async def add_purchase(
        self,
        *,
        product_id: int,
        amount: float,
        unit_price: float | None,
        purchased_date: str | None,
        best_before_date: str | None,
        store_id: int | None,
    ) -> Any:
        body: dict[str, Any] = {
            "amount": amount,
            "transaction_type": "purchase",
        }
        if unit_price is not None:
            body["price"] = round(unit_price, 4)
        if purchased_date:
            body["purchased_date"] = purchased_date
        if best_before_date:
            body["best_before_date"] = best_before_date
        if store_id is not None:
            body["shopping_location_id"] = store_id
        return await self._request(
            "POST", f"stock/products/{product_id}/add", json=body
        )
