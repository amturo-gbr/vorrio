from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_markers(path: str, markers: tuple[str, ...]) -> list[str]:
    content = (ROOT / path).read_text(encoding="utf-8")
    return [f"{path}: missing {marker!r}" for marker in markers if marker not in content]


def main() -> None:
    failures: list[str] = []
    failures.extend(
        require_markers(
            ".github/ISSUE_TEMPLATE/language_request.yml",
            (
                "name: New language",
                "id: locale",
                "id: fluency",
                "id: machine_translation",
                "independent fluent review",
                "AGPL-3.0-or-later and DCO sign-off",
            ),
        )
    )
    failures.extend(
        require_markers(
            ".github/PULL_REQUEST_TEMPLATE/language_pack.md",
            (
                "## Language pack",
                "Tracking issue: Fixes #",
                "Independent fluent reviewer",
                "make language-pack-check",
                "Signed-off-by: Name <email>",
            ),
        )
    )
    failures.extend(
        require_markers(
            ".github/PULL_REQUEST_TEMPLATE.md",
            ("PULL_REQUEST_TEMPLATE/language_pack.md", "New language"),
        )
    )
    failures.extend(
        require_markers(
            ".github/CODEOWNERS",
            (
                "* @adrian-amturo",
                "/frontend/src/locales/ @adrian-amturo",
                "/language-packs/ @adrian-amturo",
                "/scripts/validate_language_pack.py @adrian-amturo",
            ),
        )
    )
    failures.extend(
        require_markers(
            "docs/en/TRANSLATION-COMMUNITY.md",
            (
                "language:requested",
                "language:in-progress",
                "language:needs-review",
                "language:verified",
                "language:official",
                "python3 scripts/create_language_pack.py",
                "second independent language check",
            ),
        )
    )
    for path in ("README.md", "CONTRIBUTING.md", "docs/en/LOCALIZATION.md"):
        failures.extend(require_markers(path, ("TRANSLATION-COMMUNITY.md",)))

    if failures:
        raise SystemExit("\n".join(failures))
    print("Translation community contract is valid")


if __name__ == "__main__":
    main()
