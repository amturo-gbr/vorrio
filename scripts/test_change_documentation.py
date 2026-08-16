from __future__ import annotations

import unittest

from scripts.check_change_documentation import documentation_failures


class DocumentationChangeGateTests(unittest.TestCase):
    def test_behavior_change_requires_changelog_and_paired_docs(self) -> None:
        failures = documentation_failures({"frontend/src/App.tsx"})
        self.assertIn("application or deployment changes require CHANGELOG.md", failures)
        self.assertTrue(any("docs/en/" in failure for failure in failures))
        self.assertTrue(any("docs/de/" in failure for failure in failures))

    def test_paired_behavior_documentation_passes(self) -> None:
        self.assertEqual(
            documentation_failures(
                {
                    "backend/app/main.py",
                    "CHANGELOG.md",
                    "docs/en/API.md",
                    "docs/de/API.md",
                    "docs/api/openapi.json",
                    "docs/api/openapi.de.json",
                }
            ),
            [],
        )

    def test_one_sided_translation_is_rejected(self) -> None:
        self.assertEqual(
            documentation_failures({"docs/en/INSTALLATION.md"}),
            ["docs/en/INSTALLATION.md changed without docs/de/INSTALLATION.md"],
        )

    def test_deployment_change_requires_deployment_documentation(self) -> None:
        failures = documentation_failures(
            {
                "Dockerfile",
                "CHANGELOG.md",
                "docs/en/API.md",
                "docs/de/API.md",
            }
        )
        self.assertTrue(any("deployment changes require INSTALLATION.md" in failure for failure in failures))

    def test_tests_only_change_does_not_require_user_documentation(self) -> None:
        self.assertEqual(documentation_failures({"backend/tests/test_app.py"}), [])


if __name__ == "__main__":
    unittest.main()
