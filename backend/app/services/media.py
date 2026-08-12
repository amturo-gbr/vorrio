from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


class MediaValidationError(RuntimeError):
    pass


def validate_image_upload(raw: bytes, content_type: str, max_pixels: int) -> None:
    """Validate supported image containers and reject unreasonable dimensions."""
    if content_type == "image/heic":
        brand = raw[4:12].lower()
        if len(raw) < 16 or b"ftyp" not in brand or not any(
            marker in brand for marker in (b"heic", b"heif", b"mif1", b"msf1")
        ):
            raise MediaValidationError("Die HEIC-Datei ist ungültig oder beschädigt")
        return

    expected_formats = {
        "image/jpeg": {"JPEG"},
        "image/png": {"PNG"},
        "image/webp": {"WEBP"},
    }
    try:
        with Image.open(BytesIO(raw)) as image:
            if image.format not in expected_formats.get(content_type, set()):
                raise MediaValidationError(
                    "Bildinhalt und angegebener Dateityp passen nicht zusammen"
                )
            width, height = image.size
            if width < 1 or height < 1 or width * height > max_pixels:
                raise MediaValidationError(
                    "Das Bild hat zu viele Pixel. Bitte Auflösung oder Zuschnitt verkleinern"
                )
            image.verify()
    except MediaValidationError:
        raise
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as exc:
        raise MediaValidationError("Das Bild ist ungültig oder beschädigt") from exc


def prepare_product_image(raw: bytes, content_type: str, max_pixels: int) -> bytes:
    """Validate, orient and normalize a household product photo to metadata-free WebP."""
    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise MediaValidationError("Produktbilder müssen JPEG, PNG oder WebP sein")
    validate_image_upload(raw, content_type, max_pixels)
    try:
        with Image.open(BytesIO(raw)) as source:
            image = ImageOps.exif_transpose(source)
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            output = BytesIO()
            image.save(output, format="WEBP", quality=85, method=6)
            return output.getvalue()
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as exc:
        raise MediaValidationError("Das Produktbild konnte nicht verarbeitet werden") from exc
