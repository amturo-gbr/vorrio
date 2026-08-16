from __future__ import annotations

import base64
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
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
        if 'rel="canonical" href="https://vorrio.app' not in page.read_text(encoding="utf-8"):
            failures.append(f"{page.name}: canonical vorrio.app URL is missing")
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

    website_css = (WEBSITE / "styles.css").read_text(encoding="utf-8")
    if "receipt-backdrop" in website_css:
        failures.append("styles.css: decorative receipt backdrop must not obscure product media")
    for marker in (
        "top: auto;\n    right: 7%;\n    bottom: 44px;\n    width: 87%;",
        "top: auto;\n    right: 2%;\n    bottom: 8px;\n    left: auto;\n    width: 23%;",
        "top: 24%;\n    right: 3%;\n    bottom: auto;\n    left: auto;\n    width: 23%;",
        "padding: 2px;\n  overflow: hidden;\n  border: 2px solid #111517;\n  border-radius: 12% / 6%;",
        "border: 3px solid #14191b;\n  border-radius: 12% / 6%;",
    ):
        if marker not in website_css:
            failures.append("styles.css: responsive product media composition contract changed")
            break

    expected_github = "https://github.com/amturo-gbr/vorrio"
    structured_data_hashes: set[str] = set()
    for locale in ("de", "en"):
        page_text = pages[locale].read_text(encoding="utf-8")
        docs_locale = locale
        if expected_github not in page_text:
            failures.append(f"{pages[locale].name}: canonical GitHub repository link is missing")
        for marker in (
            'id="roadmap"',
            f"https://docs.vorrio.app/{docs_locale}/ROADMAP",
            f"https://docs.vorrio.app/{docs_locale}/INSTALLATION",
            f"https://docs.vorrio.app/{docs_locale}/api-reference",
            "PWA",
            "iOS",
            "Android",
            "feature_request.yml",
        ):
            if marker not in page_text:
                failures.append(f"{pages[locale].name}: roadmap marker {marker!r} is missing")
        if "GitHub Sponsors" in page_text or "github.com/sponsors/" in page_text:
            failures.append(f"{pages[locale].name}: GitHub Sponsors must stay hidden")
        for marker in (
            'data-support-link="oneTime"',
            'data-support-link="monthly5"',
            'data-support-link="monthly10"',
            'data-support-link="monthly25"',
            'data-support-link="portal"',
            'src="support-config.js"',
            'src="support.js"',
        ):
            if marker not in page_text:
                failures.append(f"{pages[locale].name}: live support marker {marker!r} is missing")
        expected_social_card = f"assets/vorrio-social-card-{locale}.png"
        seo_markers = (
            'name="robots" content="index, follow, max-image-preview:large"',
            'property="og:site_name" content="Vorrio"',
            f'property="og:image" content="https://vorrio.app/{expected_social_card}"',
            'property="og:image:width" content="1200"',
            'property="og:image:height" content="630"',
            'name="twitter:card" content="summary_large_image"',
            f'name="twitter:image" content="https://vorrio.app/{expected_social_card}"',
            'rel="apple-touch-icon"',
            'type="application/ld+json"',
        )
        for marker in seo_markers:
            if marker not in page_text:
                failures.append(f"{pages[locale].name}: SEO marker {marker!r} is missing")
        structured_match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>', page_text, re.DOTALL
        )
        if structured_match:
            try:
                structured_data = json.loads(structured_match.group(1))
            except json.JSONDecodeError as error:
                failures.append(f"{pages[locale].name}: invalid JSON-LD: {error}")
            else:
                if structured_data.get("@type") != "SoftwareApplication":
                    failures.append(
                        f"{pages[locale].name}: JSON-LD must describe a SoftwareApplication"
                    )
                if structured_data.get("codeRepository") != expected_github:
                    failures.append(
                        f"{pages[locale].name}: JSON-LD repository identity is incorrect"
                    )
            digest = hashlib.sha256(structured_match.group(1).encode("utf-8")).digest()
            structured_data_hashes.add("sha256-" + base64.b64encode(digest).decode("ascii"))

    expected_roadmap_copy = {
        "de": "Richtung stabile 1.0",
        "en": "Toward a stable 1.0",
    }
    for locale, marker in expected_roadmap_copy.items():
        if marker not in pages[locale].read_text(encoding="utf-8"):
            failures.append(f"{pages[locale].name}: current public roadmap copy is missing")
    roadmap_source = (ROOT / "docs" / "en" / "ROADMAP.md").read_text(encoding="utf-8")
    next_milestone_match = re.search(
        r"## Next family-ready PWA milestone(.*?)(?=\n## |\Z)",
        roadmap_source,
        re.DOTALL,
    )
    if next_milestone_match and "Home Assistant" in next_milestone_match.group(1):
        failures.append("docs/en/ROADMAP.md: unplanned Home Assistant milestone remains")

    for locale in ("de-imprint", "en-imprint", "de-privacy", "en-privacy"):
        page_text = pages[locale].read_text(encoding="utf-8")
        if 'name="robots" content="noindex, follow"' not in page_text:
            failures.append(f"{pages[locale].name}: legal page noindex policy is missing")
        if 'rel="apple-touch-icon"' not in page_text:
            failures.append(f"{pages[locale].name}: Apple touch icon is missing")

    for locale in ("de", "en"):
        card = WEBSITE / "assets" / f"vorrio-social-card-{locale}.png"
        if not card.exists():
            failures.append(f"{card.name}: social sharing image is missing")
            continue
        payload = card.read_bytes()
        if payload[:8] != b"\x89PNG\r\n\x1a\n" or len(payload) < 24:
            failures.append(f"{card.name}: social sharing image must be a valid PNG")
            continue
        width, height = struct.unpack(">II", payload[16:24])
        if (width, height) != (1200, 630):
            failures.append(
                f"{card.name}: social sharing image must be 1200x630, got {width}x{height}"
            )

    robots = (WEBSITE / "robots.txt").read_text(encoding="utf-8")
    if "User-agent: *" not in robots or "Sitemap: https://vorrio.app/sitemap.xml" not in robots:
        failures.append("robots.txt: crawl and sitemap directives are incomplete")

    sitemap_path = WEBSITE / "sitemap.xml"
    try:
        sitemap_root = ET.parse(sitemap_path).getroot()
    except ET.ParseError as error:
        failures.append(f"sitemap.xml: invalid XML: {error}")
    else:
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls = {
            element.text
            for element in sitemap_root.findall("sm:url/sm:loc", namespace)
            if element.text
        }
        if sitemap_urls != {"https://vorrio.app/", "https://vorrio.app/index-en.html"}:
            failures.append("sitemap.xml: must contain exactly the two indexable language pages")

    support_config = (WEBSITE / "support-config.js").read_text(encoding="utf-8")
    expected_support_links = {
        "oneTime": "https://buy.stripe.com/6oU28r3B368g7PTdjN7kc00",
        "monthly5": "https://buy.stripe.com/cNi8wPb3veEM5HL2F97kc01",
        "monthly10": "https://buy.stripe.com/cNiaEX3B3aow7PT5Rl7kc02",
        "monthly25": "https://buy.stripe.com/9B614ngnPgMU5HL7Zt7kc03",
        "portal": "https://billing.stripe.com/p/login/6oU28r3B368g7PTdjN7kc00",
    }
    for key, expected_value in expected_support_links.items():
        match = re.search(rf"{key}:\s*'([^']*)'", support_config)
        if not match:
            failures.append(f"support-config.js: missing {key} public URL")
            continue
        value = match.group(1)
        parsed = urlsplit(value)
        if value != expected_value or parsed.scheme != "https" or parsed.path.startswith("/test_"):
            failures.append(f"support-config.js: {key} must use the approved live Stripe URL")
    if re.search(r"\b(?:sk|pk|rk)_(?:test|live)_|\bwhsec_", support_config):
        failures.append("support-config.js: Stripe API and webhook keys are forbidden")

    support_script = "\n".join(
        (WEBSITE / filename).read_text(encoding="utf-8")
        for filename in ("script.js", "support.js")
    )
    for marker in ("buy.stripe.com", "billing.stripe.com", "data-support-link"):
        if marker not in support_script:
            failures.append(f"support.js: live support guard {marker!r} is missing")

    vercel_ignore = (WEBSITE / ".vercelignore").read_text(encoding="utf-8").splitlines()
    if "support-config.js" in vercel_ignore:
        failures.append(".vercelignore: live Stripe support config must be deployed")
    if "social-card-source.html" not in vercel_ignore:
        failures.append(".vercelignore: social card source must not be deployed")

    legal_source = "\n".join(
        pages[key].read_text(encoding="utf-8")
        for key in ("de-imprint", "en-imprint", "de-privacy", "en-privacy")
    )
    legal_markers = {
        "full legal entity": "Amturo UG (haftungsbeschränkt)",
        "commercial register": "HRB 12569",
        "privacy contact": "info@amturo.de",
        "privacy no-cookie statement": "keine Cookies",
        "privacy hosting provider": "Vercel Inc.",
        "privacy transfer safeguards": "EU-Standardvertragsklauseln",
    }
    for label, marker in legal_markers.items():
        if marker not in legal_source:
            failures.append(f"legal pages: missing {label}")

    public_copy = "\n".join(page.read_text(encoding="utf-8") for page in pages.values())
    internal_or_inactive_markers = (
        "Wird vorbereitet:",
        "In preparation:",
        "vor der öffentlichen Ankündigung",
        "before the public announcement",
        "muss vor dem öffentlichen Start",
        "Before the public launch",
    )
    for marker in internal_or_inactive_markers:
        if marker in public_copy:
            failures.append(f"public website: internal or inactive copy remains: {marker}")

    implementation_source = "\n".join(
        [
            pages["de"].read_text(encoding="utf-8"),
            pages["en"].read_text(encoding="utf-8"),
            support_config,
            support_script,
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

    vercel_config = json.loads((WEBSITE / "vercel.json").read_text(encoding="utf-8"))
    configured_headers = {
        header["key"].lower(): header["value"]
        for rule in vercel_config.get("headers", [])
        for header in rule.get("headers", [])
    }
    for required_header in (
        "content-security-policy",
        "permissions-policy",
        "referrer-policy",
        "strict-transport-security",
        "x-content-type-options",
        "x-frame-options",
    ):
        if required_header not in configured_headers:
            failures.append(f"vercel.json: missing security header {required_header}")
    if "connect-src 'none'" not in configured_headers.get("content-security-policy", ""):
        failures.append("vercel.json: CSP must keep outbound browser connections disabled")
    for structured_hash in structured_data_hashes:
        if f"'{structured_hash}'" not in configured_headers.get("content-security-policy", ""):
            failures.append("vercel.json: CSP must allow the exact structured-data block hash")

    css = (WEBSITE / "styles.css").read_text(encoding="utf-8")
    responsive_css = {
        "320 px minimum viewport": r"body\s*\{[^}]*min-width:\s*320px",
        "bounded page shell": r"\.shell\s*\{[^}]*width:\s*min\(100%,\s*var\(--shell\)\)",
        "390 px layout breakpoint": r"@media\s*\(max-width:\s*390px\)",
        "responsive media": r"img\s*\{[^}]*max-width:\s*100%",
        "author-level hidden state": r"\[hidden\]\s*\{[^}]*display:\s*none\s*!important",
    }
    for label, pattern in responsive_css.items():
        if not re.search(pattern, css, re.DOTALL):
            failures.append(f"styles.css: missing {label}")

    if failures:
        raise SystemExit("\n".join(failures))
    print(
        "Website contract is valid "
        "(bilingual pages, public docs links, SEO, legal data, local assets and no tracking)"
    )


if __name__ == "__main__":
    main()
