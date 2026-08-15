from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIST = DOCS / ".vitepress" / "dist"


def main() -> None:
    failures: list[str] = []

    package = json.loads((DOCS / "package.json").read_text(encoding="utf-8"))
    if package.get("devDependencies", {}).get("vitepress") != "1.6.4":
        failures.append("docs/package.json: VitePress must stay exactly pinned")
    if package.get("dependencies"):
        failures.append("docs/package.json: the static site must not have runtime dependencies")

    source_contract = DOCS / "api" / "openapi.json"
    prepared_contract = DOCS / "public" / "openapi.json"
    built_contract = DIST / "openapi.json"
    source_bytes = source_contract.read_bytes()
    for path in (prepared_contract, built_contract):
        if not path.exists() or path.read_bytes() != source_bytes:
            failures.append(f"{path.relative_to(ROOT)}: must match docs/api/openapi.json exactly")

    contract = json.loads(source_bytes)
    if contract.get("openapi") != "3.1.0":
        failures.append("docs/api/openapi.json: expected OpenAPI 3.1.0")
    operation_count = sum(
        1
        for path_item in contract.get("paths", {}).values()
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    )
    if operation_count != 103:
        failures.append(f"docs/api/openapi.json: expected 103 operations, found {operation_count}")

    localized_api = json.loads((DOCS / "api" / "openapi.de.json").read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if localized_api.get("sourceSha256") != source_hash:
        failures.append("docs/api/openapi.de.json: German API explanations are stale")
    expected_operation_keys = {
        f"{method.lower()} {api_path}"
        for api_path, path_item in contract.get("paths", {}).items()
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    localized_operations = localized_api.get("operations", {})
    if set(localized_operations) != expected_operation_keys:
        failures.append("docs/api/openapi.de.json: operation set differs from the canonical contract")
    for key in expected_operation_keys:
        source_method, source_path = key.split(" ", 1)
        source_operation = contract["paths"][source_path][source_method]
        localization = localized_operations.get(key, {})
        if not localization.get("summary"):
            failures.append(f"docs/api/openapi.de.json: missing summary for {key}")
        if source_operation.get("description") and not localization.get("description"):
            failures.append(f"docs/api/openapi.de.json: missing description for {key}")

    required_outputs = {
        "index.html": ("Sprache wählen", "Choose language"),
        "de/index.html": ("Willkommen in Vorrio", "Beginnen Sie in drei Schritten"),
        "en/index.html": ("Welcome to Vorrio", "Start in three steps"),
        "de/api-reference.html": ("Vorrio-API-Referenz", "103 / 103 Operationen", "/api/health"),
        "en/api-reference.html": ("Vorrio API reference", "103 / 103 operations", "/api/health"),
        "de/INSTALLATION.html": ("Installation", "Docker Compose"),
        "en/INSTALLATION.html": ("Installation", "Docker Compose"),
        "de/ROADMAP.html": ("Roadmap",),
        "en/ROADMAP.html": ("Roadmap", "stable public release"),
        "robots.txt": ("Sitemap: https://docs.vorrio.app/sitemap.xml",),
        "sitemap.xml": ("https://docs.vorrio.app/de/", "https://docs.vorrio.app/en/api-reference"),
    }
    for relative, markers in required_outputs.items():
        path = DIST / relative
        if not path.exists():
            failures.append(f"docs build: missing {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"docs build: {relative} is missing {marker!r}")

    api_component = (DOCS / ".vitepress/theme/components/ApiReference.vue").read_text(
        encoding="utf-8"
    )
    if '../../../api/openapi.json' not in api_component:
        failures.append("API reference must import the canonical checked-in OpenAPI file")
    if '../../../api/openapi.de.json' not in api_component:
        failures.append("API reference must import the checked German explanation layer")
    for forbidden in ("Try it", "fetch(", "axios", "Authorization: Bearer"):
        if forbidden in api_component:
            failures.append(f"API reference must stay read-only: found {forbidden!r}")

    docs_vercel = json.loads((DOCS / "vercel.json").read_text(encoding="utf-8"))
    if docs_vercel.get("outputDirectory") != ".vitepress/dist":
        failures.append("docs/vercel.json: static VitePress output directory is incorrect")
    configured_headers = {
        header["key"].lower(): header["value"]
        for rule in docs_vercel.get("headers", [])
        for header in rule.get("headers", [])
    }
    for required in (
        "content-security-policy",
        "referrer-policy",
        "strict-transport-security",
        "x-content-type-options",
        "x-frame-options",
    ):
        if required not in configured_headers:
            failures.append(f"docs/vercel.json: missing security header {required}")

    theme_css = (DOCS / ".vitepress/theme/custom.css").read_text(encoding="utf-8")
    if "height: calc(100dvh - var(--vp-nav-height));" not in theme_css:
        failures.append("docs theme: mobile navigation must fill the available viewport height")

    if failures:
        raise SystemExit("\n".join(failures))
    print(
        "Docs site contract is valid "
        f"({operation_count} static API operations, canonical OpenAPI asset and hardened output)"
    )


if __name__ == "__main__":
    main()
