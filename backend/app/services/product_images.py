from __future__ import annotations

import os
import uuid
from pathlib import Path


MANAGED_PRODUCT_IMAGE_PREFIX = "/api/v1/catalog/products/"
MANAGED_PRODUCT_IMAGE_SUFFIX = "/image"


def managed_product_image_url(product_id: str) -> str:
    return f"{MANAGED_PRODUCT_IMAGE_PREFIX}{uuid.UUID(product_id)}{MANAGED_PRODUCT_IMAGE_SUFFIX}"


def is_managed_product_image_url(value: str | None, product_id: str | None = None) -> bool:
    if not value or not value.startswith(MANAGED_PRODUCT_IMAGE_PREFIX) or not value.endswith(
        MANAGED_PRODUCT_IMAGE_SUFFIX
    ):
        return False
    raw_id = value[len(MANAGED_PRODUCT_IMAGE_PREFIX) : -len(MANAGED_PRODUCT_IMAGE_SUFFIX)]
    try:
        parsed_id = str(uuid.UUID(raw_id))
    except ValueError:
        return False
    return product_id is None or parsed_id == str(uuid.UUID(product_id))


class ProductImageStore:
    def __init__(self, data_dir: Path) -> None:
        self.root = (data_dir / "product-images").resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, product_id: str) -> Path:
        normalized_id = str(uuid.UUID(product_id))
        return self.root / f"{normalized_id}.webp"

    def stage(self, product_id: str, body: bytes) -> Path:
        destination = self.path(product_id)
        staged = self.root / f".{destination.stem}.{uuid.uuid4()}.upload"
        staged.write_bytes(body)
        return staged

    def commit(self, product_id: str, staged: Path) -> Path:
        destination = self.path(product_id)
        os.replace(staged, destination)
        return destination

    @staticmethod
    def discard(staged: Path) -> None:
        staged.unlink(missing_ok=True)

    def delete(self, product_id: str) -> bool:
        path = self.path(product_id)
        existed = path.is_file()
        path.unlink(missing_ok=True)
        return existed
