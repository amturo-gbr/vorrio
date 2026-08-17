from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / "frontend" / "src" / "locales"
COMMUNITY_PACKS = ROOT / "language-packs" / "community"
MAX_CATALOG_BYTES = 2 * 1024 * 1024
LOCALE_PATTERN = re.compile(
    r"^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$"
)
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Za-z0-9_.-]+)\s*}}")
HTML_PATTERN = re.compile(r"<\s*/?\s*[A-Za-z!][^>]*>")
UNSAFE_URI_PATTERN = re.compile(
    r"(?:javascript\s*:|data\s*:\s*(?:text/html|application/javascript))",
    re.IGNORECASE,
)
ALLOWED_CAPABILITIES = {
    "frontend",
    "backend",
    "notifications",
    "pwa_manifest",
}
REQUIRED_MANIFEST_FIELDS = {
    "$schema",
    "schema_version",
    "locale",
    "native_name",
    "english_name",
    "direction",
    "fallback_locale",
    "tier",
    "catalog_mode",
    "catalog_version",
    "minimum_vorrio_version",
    "completion",
    "capabilities",
}


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: invalid UTF-8 JSON ({error})") from error


def placeholders(value: str) -> set[str]:
    return set(PLACEHOLDER_PATTERN.findall(value))


def validate_pack(pack_dir: Path, canonical_catalog: dict[str, str]) -> list[str]:
    errors: list[str] = []
    canonical_keys = set(canonical_catalog)
    if not pack_dir.is_dir():
        return [f"{pack_dir}: language pack directory does not exist"]

    expected_files = {"manifest.json", "translation.json"}
    actual_files = {path.name for path in pack_dir.iterdir() if path.is_file()}
    unexpected = sorted(actual_files - expected_files)
    missing_files = sorted(expected_files - actual_files)
    if unexpected:
        errors.append(f"{pack_dir}: unexpected files: {', '.join(unexpected)}")
    if missing_files:
        errors.append(f"{pack_dir}: missing files: {', '.join(missing_files)}")
        return errors

    manifest = read_json(pack_dir / "manifest.json")
    catalog_path = pack_dir / "translation.json"
    catalog = read_json(catalog_path)
    if not isinstance(manifest, dict):
        return errors + [f"{pack_dir}: manifest must be a JSON object"]
    if not isinstance(catalog, dict):
        return errors + [f"{pack_dir}: translation catalog must be a JSON object"]

    manifest_fields = set(manifest)
    missing_fields = sorted(REQUIRED_MANIFEST_FIELDS - manifest_fields)
    extra_fields = sorted(manifest_fields - REQUIRED_MANIFEST_FIELDS)
    if missing_fields:
        errors.append(f"{pack_dir}: missing manifest fields: {', '.join(missing_fields)}")
    if extra_fields:
        errors.append(f"{pack_dir}: unsupported manifest fields: {', '.join(extra_fields)}")

    locale = manifest.get("locale")
    if not isinstance(locale, str) or not LOCALE_PATTERN.fullmatch(locale):
        errors.append(f"{pack_dir}: locale must be a canonical BCP 47 language tag")
    elif pack_dir.name != locale:
        errors.append(f"{pack_dir}: directory name must match locale {locale!r}")
    if manifest.get("schema_version") != 1:
        errors.append(f"{pack_dir}: only schema_version 1 is supported")
    if manifest.get("direction") not in {"ltr", "rtl"}:
        errors.append(f"{pack_dir}: direction must be ltr or rtl")
    if manifest.get("tier") not in {"official", "community"}:
        errors.append(f"{pack_dir}: tier must be official or community")
    if manifest.get("catalog_mode") not in {"complete", "source-fallback"}:
        errors.append(f"{pack_dir}: catalog_mode must be complete or source-fallback")
    if not VERSION_PATTERN.fullmatch(str(manifest.get("minimum_vorrio_version", ""))):
        errors.append(f"{pack_dir}: minimum_vorrio_version must use MAJOR.MINOR.PATCH")
    if not isinstance(manifest.get("catalog_version"), int) or manifest.get("catalog_version", 0) < 1:
        errors.append(f"{pack_dir}: catalog_version must be a positive integer")
    if not isinstance(manifest.get("completion"), int) or not 0 <= manifest.get("completion", -1) <= 100:
        errors.append(f"{pack_dir}: completion must be an integer from 0 through 100")
    for name_field in ("native_name", "english_name"):
        value = manifest.get(name_field)
        if not isinstance(value, str) or not 2 <= len(value.strip()) <= 80:
            errors.append(f"{pack_dir}: {name_field} must contain 2 through 80 characters")

    capabilities = manifest.get("capabilities")
    if (
        not isinstance(capabilities, list)
        or not capabilities
        or len(capabilities) != len(set(map(str, capabilities)))
        or any(value not in ALLOWED_CAPABILITIES for value in capabilities)
    ):
        errors.append(f"{pack_dir}: capabilities contain an unsupported or duplicate value")

    if catalog_path.stat().st_size > MAX_CATALOG_BYTES:
        errors.append(f"{pack_dir}: catalog exceeds the 2 MiB size limit")
    invalid_values = sorted(key for key, value in catalog.items() if not isinstance(key, str) or not isinstance(value, str))
    if invalid_values:
        errors.append(f"{pack_dir}: every catalog key and value must be a string")
        return errors

    catalog_keys = set(catalog)
    if manifest.get("catalog_mode") == "complete":
        missing_keys = sorted(canonical_keys - catalog_keys)
        if missing_keys:
            errors.append(f"{pack_dir}: complete catalog is missing {len(missing_keys)} keys")
    unknown_keys = sorted(catalog_keys - canonical_keys)
    if unknown_keys:
        errors.append(f"{pack_dir}: catalog contains {len(unknown_keys)} unknown keys")

    unsafe: list[str] = []
    placeholder_errors: list[str] = []
    empty: list[str] = []
    for key, value in catalog.items():
        if not value.strip():
            empty.append(key)
        if HTML_PATTERN.search(value) or UNSAFE_URI_PATTERN.search(value) or "\x00" in value:
            unsafe.append(key)
        if key in canonical_catalog and placeholders(canonical_catalog[key]) != placeholders(value):
            placeholder_errors.append(key)
    if empty:
        errors.append(f"{pack_dir}: catalog contains {len(empty)} empty translations")
    if unsafe:
        errors.append(f"{pack_dir}: catalog contains {len(unsafe)} HTML, unsafe URI or NUL values")
    if placeholder_errors:
        errors.append(f"{pack_dir}: catalog changes placeholders in {len(placeholder_errors)} entries")

    calculated_completion = round(100 * len(catalog_keys & canonical_keys) / len(canonical_keys))
    if (
        manifest.get("tier") == "community"
        or manifest.get("catalog_mode") == "complete"
    ) and manifest.get("completion") != calculated_completion:
        errors.append(
            f"{pack_dir}: completion is {manifest.get('completion')}, calculated {calculated_completion}"
        )
    return errors


def repository_pack_dirs() -> list[Path]:
    official = {
        path for path in LOCALES.iterdir() if path.is_dir() and not path.name.startswith(".")
    }
    community = (
        {
            path
            for path in COMMUNITY_PACKS.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        if COMMUNITY_PACKS.exists()
        else set()
    )
    return sorted(official | community)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Vorrio language packs")
    parser.add_argument("pack", nargs="?", type=Path, help="language pack directory")
    args = parser.parse_args()

    canonical = read_json(LOCALES / "en" / "translation.json")
    if not isinstance(canonical, dict):
        raise SystemExit("English canonical catalog must be a JSON object")
    pack_dirs = [args.pack.resolve()] if args.pack else repository_pack_dirs()
    failures = [error for pack_dir in pack_dirs for error in validate_pack(pack_dir, canonical)]
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Language pack contract is valid ({len(pack_dirs)} packs, {len(canonical)} canonical keys)")


if __name__ == "__main__":
    main()
