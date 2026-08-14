from __future__ import annotations

import re
from dataclasses import dataclass


class BarcodeValidationError(ValueError):
    pass


@dataclass(frozen=True)
class NormalizedBarcode:
    raw: str
    value: str
    symbology: str

    @property
    def supports_open_facts_lookup(self) -> bool:
        """Only standardized retail GTINs are safe to query externally."""
        return len(self.value) in GTIN_SYMBOLOGIES


GTIN_SYMBOLOGIES = {
    8: "EAN-8",
    12: "UPC-A",
    13: "EAN-13",
    14: "GTIN-14",
}


def normalize_barcode(value: str) -> NormalizedBarcode:
    raw = value.strip()
    normalized = re.sub(r"[\s-]+", "", raw)
    if not normalized.isdigit() or not 4 <= len(normalized) <= 18:
        raise BarcodeValidationError("Der Code muss aus 4 bis 18 Ziffern bestehen")
    if len(normalized) in GTIN_SYMBOLOGIES and len(set(normalized)) == 1:
        raise BarcodeValidationError("Der erkannte Code ist nicht plausibel")
    if len(normalized) in GTIN_SYMBOLOGIES and not has_valid_gtin_checksum(normalized):
        raise BarcodeValidationError("Die Prüfziffer des Barcodes ist ungültig")
    return NormalizedBarcode(
        raw=raw,
        value=normalized,
        symbology=GTIN_SYMBOLOGIES.get(len(normalized), "Interner Code"),
    )


def has_valid_gtin_checksum(value: str) -> bool:
    digits = [int(character) for character in value]
    expected = (10 - sum(
        digit * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(digits[:-1]))
    ) % 10) % 10
    return expected == digits[-1]


def parse_package_quantity(value: str | None) -> tuple[float | None, str | None]:
    if not value:
        return None, None
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*([A-Za-zÄÖÜäöü]+)", value)
    if not match:
        return None, None
    return float(match.group(1).replace(",", ".")), match.group(2)
