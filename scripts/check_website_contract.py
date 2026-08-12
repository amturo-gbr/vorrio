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
        self.viewport = ""
        self.links: list[str] = []
        self.alternates: set[str] = set()
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.html_lang = values.get("lang") or ""
        if tag == "meta" and values.get("name") == "viewport":
            self.viewport = values.get("content") or ""
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
    pages = {
        "de": WEBSITE / "index.html",
        "en": WEBSITE / "index-en.html",
        "de-imprint": WEBSITE / "impressum.html",
        "en-imprint": WEBSITE / "imprint.html",
        "de-privacy": WEBSITE / "datenschutz.html",
        "en-privacy": WEBSITE / "privacy.html",
    }
    page_locales = {
        "de": "de",
        "en": "en",
        "de-imprint": "de",
        "en-imprint": "en",
        "de-privacy": "de",
        "en-privacy": "en",
    }
    parsers: dict[str, WebsiteParser] = {}

    for locale, page in pages.items():
        parser = WebsiteParser()
        parser.feed(page.read_text(encoding="utf-8"))
        parsers[locale] = parser
        if parser.html_lang != page_locales[locale]:
            failures.append(f"{page.name}: html lang must be {page_locales[locale]}")
        if not {"width=device-width", "initial-scale=1"}.issubset(
            {value.strip() for value in parser.viewport.split(",")}
        ):
            failures.append(f"{page.name}: responsive viewport contract is missing")
        if not {"de", "en", "x-default"}.issubset(parser.alternates):
            failures.append(f"{page.name}: missing de/en/x-default alternate links")
        for target in parser.links:
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or target.startswith(("#", "mailto:")):
                continue
            local_target = WEBSITE / parsed.path
            if not local_target.exists():
                failures.append(f"{page.name}: missing local asset {parsed.path}")

    english_text = " ".join(parsers["en"].text).replace(
        "Amturo UG (haftungsbeschränkt)", "Amturo UG"
    )
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

    expected_github = "https://github.com/amturo-gbr/vorrio"
    for locale in ("de", "en"):
        page_text = pages[locale].read_text(encoding="utf-8")
        if expected_github not in page_text:
            failures.append(f"{pages[locale].name}: canonical GitHub repository link is missing")
        if "github.com/sponsors/" in page_text:
            failures.append(f"{pages[locale].name}: inactive GitHub Sponsors link must not be published")

    legal_source = "\n".join(
        pages[key].read_text(encoding="utf-8")
        for key in ("de-imprint", "en-imprint", "de-privacy", "en-privacy")
    )
    legal_markers = {
        "full legal entity": "Amturo UG (haftungsbeschränkt)",
        "commercial register": "HRB 12569",
        "privacy contact": "info@amturo.de",
        "privacy no-cookie statement": "keine Cookies",
        "privacy hosting launch gate": "Vor Veröffentlichung zu ergänzen",
    }
    for label, marker in legal_markers.items():
        if marker not in legal_source:
            failures.append(f"legal pages: missing {label}")

    implementation_source = "\n".join(
        [
            pages["de"].read_text(encoding="utf-8"),
            pages["en"].read_text(encoding="utf-8"),
            (WEBSITE / "script.js").read_text(encoding="utf-8"),
        ]
    ).lower()
    tracking_markers = (
        "googletagmanager",
        "google-analytics",
        "plausible.io",
        "posthog",
        "document.cookie",
        "localstorage.",
        "sessionstorage.",
    )
    for marker in tracking_markers:
        if marker in implementation_source:
            failures.append(f"website implementation: unexpected tracking/storage marker {marker}")

    css = (WEBSITE / "styles.css").read_text(encoding="utf-8")
    responsive_css = {
        "320 px minimum viewport": r"body\s*\{[^}]*min-width:\s*320px",
        "bounded page shell": r"\.shell\s*\{[^}]*width:\s*min\(100%,\s*var\(--shell\)\)",
        "390 px layout breakpoint": r"@media\s*\(max-width:\s*390px\)",
        "responsive media": r"img\s*\{[^}]*max-width:\s*100%",
    }
    for label, pattern in responsive_css.items():
        if not re.search(pattern, css, re.DOTALL):
            failures.append(f"styles.css: missing {label}")

    if failures:
        raise SystemExit("\n".join(failures))
    print("Website contract is valid (bilingual pages, legal data, local assets and no tracking)")


if __name__ == "__main__":
    main()
