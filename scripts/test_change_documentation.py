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
                },
                ["- Website impact: none — Internal API refactoring only."],
            ),
            [],
        )

    def test_public_product_change_requires_website_decision(self) -> None:
        failures = documentation_failures(
            {
                "frontend/src/App.tsx",
                "CHANGELOG.md",
                "docs/en/WORKFLOW.md",
                "docs/de/WORKFLOW.md",
            }
        )
        self.assertTrue(any("public product changes require" in failure for failure in failures))

    def test_paired_public_website_update_satisfies_gate(self) -> None:
        self.assertEqual(
            documentation_failures(
                {
                    "frontend/src/App.tsx",
                    "CHANGELOG.md",
                    "docs/en/WORKFLOW.md",
                    "docs/de/WORKFLOW.md",
                    "website/index.html",
                    "website/index-en.html",
                }
            ),
            [],
        )

    def test_new_changelog_reason_satisfies_public_website_gate(self) -> None:
        self.assertEqual(
            documentation_failures(
                {
                    "backend/app/security.py",
                    "CHANGELOG.md",
                    "docs/en/IDENTITY-SECURITY.md",
                    "docs/de/IDENTITY-SECURITY.md",
                },
                ["- Website impact: none — The internal session validation flow is unchanged."],
            ),
            [],
        )

    def test_short_website_reason_does_not_bypass_gate(self) -> None:
        failures = documentation_failures(
            {
                "backend/app/security.py",
                "CHANGELOG.md",
                "docs/en/IDENTITY-SECURITY.md",
                "docs/de/IDENTITY-SECURITY.md",
            },
            ["- Website impact: none — No."],
        )
        self.assertTrue(any("public product changes require" in failure for failure in failures))

    def test_one_sided_public_website_copy_is_rejected(self) -> None:
        self.assertEqual(
            documentation_failures({"website/index.html"}),
            ["public website copy changed without website/index-en.html"],
        )

    def test_roadmap_change_requires_public_website_decision(self) -> None:
        failures = documentation_failures({"docs/en/ROADMAP.md", "docs/de/ROADMAP.md"})
        self.assertTrue(any("public product changes require" in failure for failure in failures))

    def test_localized_screenshot_change_requires_its_pair(self) -> None:
        self.assertEqual(
            documentation_failures({"website/assets/scanner-desktop.png"}),
            [
                "localized website screenshot changed without "
                "website/assets/scanner-desktop-en.png"
            ],
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
