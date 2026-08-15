from pathlib import Path
import unittest

from scripts.check_release_package import (
    FORBIDDEN_TEXT,
    forbidden_path_reason,
    forbidden_text_labels,
)


class ReleasePackageSecurityTests(unittest.TestCase):
    def test_private_and_generated_paths_are_rejected(self) -> None:
        for value in (
            ".env.local",
            "cookies.txt",
            "capture.har",
            "data/app.sqlite3",
            ".playwright-cli/page.png",
            "frontend/dist/index.html",
            "website/.vercel/output/config.json",
        ):
            with self.subTest(value=value):
                self.assertIsNotNone(forbidden_path_reason(Path(value)))

        self.assertIsNone(forbidden_path_reason(Path("docs/INSTALLATION.md")))
        self.assertIsNone(forbidden_path_reason(Path("website/assets/vorrio-icon.png")))
        self.assertIsNone(forbidden_path_reason(Path(".env.example")))

    def test_private_network_and_cloudflare_account_endpoints_are_rejected(self) -> None:
        private_address = ".".join(("192", "168", "1", "209"))
        r2_account = "ab" * 16
        self.assertIsNotNone(FORBIDDEN_TEXT["private IPv4 address"].search(private_address))
        self.assertIsNotNone(
            FORBIDDEN_TEXT["Cloudflare account endpoint"].search(
                f"https://{r2_account}.r2.cloudflarestorage.com"
            )
        )

        self.assertIsNone(
            FORBIDDEN_TEXT["private IPv4 address"].search("192.0.2.10")
        )
        self.assertIsNone(
            FORBIDDEN_TEXT["Cloudflare account endpoint"].search(
                "https://vorrio.example.com"
            )
        )

    def test_private_network_examples_are_allowlisted_only_in_exact_reviewed_files(self) -> None:
        docker_network = ".".join(("172", "20", "0", "0"))
        actual_household_address = ".".join(("192", "168", "1", "209"))

        self.assertEqual(
            forbidden_text_labels(
                Path("docs/DEPLOYMENT-PROFILES.md"),
                f"FORWARDED_ALLOW_IPS={docker_network}/16",
            ),
            set(),
        )
        self.assertEqual(
            forbidden_text_labels(Path("README.md"), docker_network),
            {"private IPv4 address"},
        )
        self.assertEqual(
            forbidden_text_labels(Path("docs/INSTALLATION.md"), actual_household_address),
            {"private IPv4 address"},
        )

    def test_development_assistant_attribution_is_rejected(self) -> None:
        assistant_name = "Code" + "x"
        self.assertEqual(
            forbidden_text_labels(
                Path("README.md"), f"This source was prepared with {assistant_name}."
            ),
            {"development-assistant attribution"},
        )


if __name__ == "__main__":
    unittest.main()
