from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"


class WebsiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.html_lang = ""
        self.links: list[str] = []
        self.alternates: set[str] = set()
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.html_lang = values.get("lang") or ""
        if tag in {"a", "link", "script", "img"}:
            target = values.get("href") or values.get("src")
            if target:
                self.links.append(target)
        if tag == "link" and values.get("rel") == "alternate" and values.get("hreflang"):
            self.alternates.add(values["hreflang"] or "")

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.text.append(data.strip())


def main() -> None:
    failures: list[str] = []
    pages = {"de": WEBSITE / "index.html", "en": WEBSITE / "index-en.html"}
    parsers: dict[str, WebsiteParser] = {}

    for locale, page in pages.items():
        parser = WebsiteParser()
        parser.feed(page.read_text(encoding="utf-8"))
        parsers[locale] = parser
        if parser.html_lang != locale:
            failures.append(f"{page.name}: html lang must be {locale}")
        if not {"de", "en", "x-default"}.issubset(parser.alternates):
            failures.append(f"{page.name}: missing de/en/x-default alternate links")
        for target in parser.links:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith(("#", "mailto:")):
                continue
            local_target = WEBSITE / parsed.path
            if not local_target.exists():
                failures.append(f"{page.name}: missing local asset {parsed.path}")

    english_text = " ".join(parsers["en"].text)
    german_copy = re.compile(
        r"[ÄÖÜäöüß]|\b(?:Dein|Einkauf|Vorrat|Bons|Funktionen|Prinzipien|Unterstützen|"
        r"Zum Inhalt|Auf GitHub|Erfassen|Prüfen|Übernehmen|Haushalt|selbst gehostet)\b"
    )
    if german_copy.search(english_text):
        failures.append("index-en.html: probable untranslated German copy remains")

    german_product_images = {
        "assets/scanner-desktop.png",
        "assets/receipt-review-mobile.jpg",
        "assets/scanner-entry-mobile.jpg",
        "assets/stock-count-desktop.png",
        "assets/shopping-list-desktop.jpg",
        "assets/catalog-editor-mobile.png",
    }
    reused_german_images = german_product_images.intersection(parsers["en"].links)
    if reused_german_images:
        failures.append(
            "index-en.html: German product screenshots reused: "
            + ", ".join(sorted(reused_german_images))
        )

    if failures:
        raise SystemExit("\n".join(failures))
    print("Website contract is valid (German and English, local assets resolved)")


if __name__ == "__main__":
    main()
