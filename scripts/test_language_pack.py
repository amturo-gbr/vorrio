from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_language_pack import LOCALES, read_json, validate_pack


class LanguagePackContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.pack = Path(self.temporary.name) / "fr"
        self.pack.mkdir()
        self.catalog = read_json(LOCALES / "en" / "translation.json")
        manifest = read_json(LOCALES / "en" / "manifest.json")
        manifest.update(
            {
                "locale": "fr",
                "native_name": "Français",
                "english_name": "French",
                "tier": "community",
                "capabilities": ["frontend"],
            }
        )
        (self.pack / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        self.write_catalog(self.catalog)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_catalog(self, catalog: dict[str, str]) -> None:
        (self.pack / "translation.json").write_text(
            json.dumps(catalog, ensure_ascii=False), encoding="utf-8"
        )

    def errors(self) -> list[str]:
        return validate_pack(self.pack, self.catalog)

    def test_complete_data_only_community_pack_is_accepted(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_executable_content_and_extra_files_are_rejected(self) -> None:
        catalog = dict(self.catalog)
        catalog["Einstellungen"] = "<script>alert(1)</script>"
        self.write_catalog(catalog)
        (self.pack / "install.js").write_text("alert(1)", encoding="utf-8")
        rendered = "\n".join(self.errors())
        self.assertIn("unexpected files", rendered)
        self.assertIn("HTML, unsafe URI or NUL", rendered)

    def test_changed_interpolation_placeholders_are_rejected(self) -> None:
        catalog = dict(self.catalog)
        key = "{{count}} Produkte_one"
        catalog[key] = "{{amount}} produit"
        self.write_catalog(catalog)
        self.assertIn("changes placeholders", "\n".join(self.errors()))

    def test_community_completion_must_match_explicit_catalog_coverage(self) -> None:
        manifest_path = self.pack / "manifest.json"
        manifest = read_json(manifest_path)
        manifest["catalog_mode"] = "source-fallback"
        manifest["completion"] = 100
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        self.write_catalog({})
        self.assertIn("completion is 100, calculated 0", "\n".join(self.errors()))


if __name__ == "__main__":
    unittest.main()
