from __future__ import annotations

import hashlib
import json
from typing import Any


def build_receipt_fingerprint(
    receipt: dict[str, Any], items: list[dict[str, Any]]
) -> str | None:
    """Build a conservative identity for the same receipt captured more than once."""
    store = _key(receipt.get("retailer") or receipt.get("store_name"))
    purchase_date = str(receipt.get("purchase_date") or "").strip()
    total = _money(receipt.get("total"))
    if not store or not purchase_date or total is None or len(items) < 2:
        return None

    line_signatures: list[tuple[str, str, str]] = []
    for item in items:
        name = _key(item.get("normalized_name") or item.get("raw_name"))
        line_total = _money(item.get("total_price"))
        quantity = _quantity(item.get("quantity"))
        if name:
            line_signatures.append((name, quantity, line_total or ""))
    if len(line_signatures) < 2:
        return None

    payload = {
        "store": store,
        "store_number": _key(receipt.get("store_number")),
        "purchase_date": purchase_date,
        "currency": str(receipt.get("currency") or "EUR").upper(),
        "total": total,
        "lines": sorted(line_signatures),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _key(value: Any) -> str:
    from ..database import canonical_receipt_key

    return canonical_receipt_key(str(value or ""))


def _money(value: Any) -> str | None:
    try:
        return f"{float(value):.2f}" if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _quantity(value: Any) -> str:
    try:
        return f"{float(value or 1):.3f}"
    except (TypeError, ValueError):
        return "1.000"
