from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.create_language_pack import create_pack
from scripts.validate_language_pack import LOCALES, read_json, validate_pack


class CreateLanguagePackTests(unittest.TestCase):
    def test_generator_creates_valid_empty_community_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = create_pack(
                Path(temporary), "es", "Español", "Spanish", direction="ltr"
            )
            manifest = json.loads(
                (pack / "manifest.json").read_text(encoding="utf-8")
            )
            catalog = json.loads(
                (pack / "translation.json").read_text(encoding="utf-8")
            )
            canonical = read_json(LOCALES / "en" / "translation.json")

            self.assertEqual(manifest["locale"], "es")
            self.assertEqual(manifest["tier"], "community")
            self.assertEqual(manifest["completion"], 0)
            self.assertEqual(catalog, {})
            self.assertEqual(validate_pack(pack, canonical), [])

    def test_generator_refuses_to_replace_an_existing_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_pack(root, "fr", "Français", "French")
            with self.assertRaises(FileExistsError):
                create_pack(root, "fr", "Français", "French")


if __name__ == "__main__":
    unittest.main()
