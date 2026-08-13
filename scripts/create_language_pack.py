from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_language_pack import LOCALE_PATTERN  # noqa: E402


DEFAULT_OUTPUT_ROOT = ROOT / "language-packs" / "community"


def create_pack(
    output_root: Path,
    locale: str,
    native_name: str,
    english_name: str,
    direction: str = "ltr",
) -> Path:
    if not LOCALE_PATTERN.fullmatch(locale):
        raise ValueError("locale must be a canonical BCP 47 language tag")
    if direction not in {"ltr", "rtl"}:
        raise ValueError("direction must be ltr or rtl")
    if not 2 <= len(native_name.strip()) <= 80:
        raise ValueError("native name must contain 2 through 80 characters")
    if not 2 <= len(english_name.strip()) <= 80:
        raise ValueError("English name must contain 2 through 80 characters")

    pack_dir = output_root / locale
    if pack_dir.exists():
        raise FileExistsError(f"language pack already exists: {pack_dir}")

    package = json.loads(
        (ROOT / "frontend" / "package.json").read_text(encoding="utf-8")
    )
    manifest = {
        "$schema": "../../schema-v1.json",
        "schema_version": 1,
        "locale": locale,
        "native_name": native_name.strip(),
        "english_name": english_name.strip(),
        "direction": direction,
        "fallback_locale": "en",
        "tier": "community",
        "catalog_mode": "source-fallback",
        "catalog_version": 1,
        "minimum_vorrio_version": package["version"],
        "completion": 0,
        "capabilities": ["frontend"],
    }

    pack_dir.mkdir(parents=True)
    (pack_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (pack_dir / "translation.json").write_text("{}\n", encoding="utf-8")
    return pack_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a safe, data-only Vorrio community language pack"
    )
    parser.add_argument("locale", help="canonical BCP 47 tag, for example es or pt-BR")
    parser.add_argument("native_name", help="language name in that language")
    parser.add_argument("english_name", help="language name in English")
    parser.add_argument("--direction", choices=("ltr", "rtl"), default="ltr")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()

    try:
        pack_dir = create_pack(
            args.output_root,
            args.locale,
            args.native_name,
            args.english_name,
            args.direction,
        )
    except (FileExistsError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print(f"Created community language pack: {pack_dir}")


if __name__ == "__main__":
    main()
