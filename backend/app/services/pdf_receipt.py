from __future__ import annotations

from io import BytesIO

import pypdfium2 as pdfium


MAX_PDF_PAGES = 4
MAX_PDF_TEXT_CHARS = 30_000
PDF_RENDER_SCALE = 2.5
MAX_RENDER_PIXELS = 40_000_000
MAX_RENDER_DIMENSION = 12_000


class PdfReceiptError(RuntimeError):
    pass


def prepare_pdf_receipt(raw: bytes) -> tuple[list[tuple[bytes, str]], str]:
    """Render a short receipt PDF to model-friendly JPEG pages and extract its text."""
    if not raw.startswith(b"%PDF-"):
        raise PdfReceiptError("Die Datei ist kein gültiges PDF")

    try:
        document = pdfium.PdfDocument(raw)
    except Exception as exc:
        raise PdfReceiptError(
            "Das PDF konnte nicht geöffnet werden. Passwortgeschützte PDFs werden nicht unterstützt."
        ) from exc

    pages: list[tuple[bytes, str]] = []
    text_parts: list[str] = []
    try:
        page_count = len(document)
        if page_count == 0:
            raise PdfReceiptError("Das PDF enthält keine Seiten")
        if page_count > MAX_PDF_PAGES:
            raise PdfReceiptError(
                f"Bitte nur Bon-PDFs mit höchstens {MAX_PDF_PAGES} Seiten hochladen"
            )

        for page_number in range(page_count):
            page = document[page_number]
            try:
                render_width = max(1, int(page.get_width() * PDF_RENDER_SCALE))
                render_height = max(1, int(page.get_height() * PDF_RENDER_SCALE))
                if (
                    render_width > MAX_RENDER_DIMENSION
                    or render_height > MAX_RENDER_DIMENSION
                    or render_width * render_height > MAX_RENDER_PIXELS
                ):
                    raise PdfReceiptError(
                        "Eine PDF-Seite ist zu groß. Bitte den Bon kleiner exportieren"
                    )
                text_page = page.get_textpage()
                try:
                    page_text = text_page.get_text_bounded().strip()
                    if page_text:
                        text_parts.append(f"--- PDF-Seite {page_number + 1} ---\n{page_text}")
                finally:
                    text_page.close()

                bitmap = page.render(scale=PDF_RENDER_SCALE)
                try:
                    image = bitmap.to_pil()
                    try:
                        if image.mode != "RGB":
                            converted = image.convert("RGB")
                        else:
                            converted = image.copy()
                        try:
                            output = BytesIO()
                            converted.save(
                                output,
                                format="JPEG",
                                quality=90,
                                optimize=True,
                            )
                            pages.append((output.getvalue(), "image/jpeg"))
                        finally:
                            converted.close()
                    finally:
                        image.close()
                finally:
                    bitmap.close()
            finally:
                page.close()
    except PdfReceiptError:
        raise
    except Exception as exc:
        raise PdfReceiptError("Das PDF ist beschädigt oder konnte nicht gerendert werden") from exc
    finally:
        document.close()

    source_text = "\n\n".join(text_parts)[:MAX_PDF_TEXT_CHARS]
    return pages, source_text
