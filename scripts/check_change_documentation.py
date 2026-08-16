from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEBSITE_PAGES = {"website/index.html", "website/index-en.html"}
WEBSITE_IMAGE_PAIRS = (
    ("website/assets/scanner-desktop.png", "website/assets/scanner-desktop-en.png"),
    ("website/assets/receipt-review-mobile.jpg", "website/assets/receipt-review-mobile-en.png"),
    ("website/assets/scanner-entry-mobile.jpg", "website/assets/scanner-entry-mobile-en.png"),
    ("website/assets/stock-count-desktop.png", "website/assets/stock-count-desktop-en.png"),
    ("website/assets/shopping-list-desktop.jpg", "website/assets/shopping-list-desktop-en.png"),
    ("website/assets/catalog-editor-mobile.png", "website/assets/catalog-editor-mobile-en.png"),
)
WEBSITE_NO_IMPACT_PREFIX = "- Website impact: none — "


def changed_files(base: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base, "--"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def added_lines(base: str, path: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--unified=0", base, "--", path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        line[1:].strip()
        for line in result.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]


def has_website_no_impact_reason(changelog_added_lines: list[str]) -> bool:
    return any(
        line.startswith(WEBSITE_NO_IMPACT_PREFIX)
        and len(line.removeprefix(WEBSITE_NO_IMPACT_PREFIX).strip()) >= 12
        for line in changelog_added_lines
    )


def documentation_failures(
    changed: set[str], changelog_added_lines: list[str] | None = None
) -> list[str]:
    failures: list[str] = []
    changelog_added_lines = changelog_added_lines or []
    behavior_changed = any(
        path.startswith("backend/app/") or path.startswith("frontend/src/")
        for path in changed
    )
    deployment_changed = bool(
        changed
        & {
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.release.yml",
            "stack.yml",
            ".env.example",
        }
    )
    docs_en = {path.removeprefix("docs/en/") for path in changed if path.startswith("docs/en/")}
    docs_de = {path.removeprefix("docs/de/") for path in changed if path.startswith("docs/de/")}
    roadmap_changed = bool(changed & {"docs/en/ROADMAP.md", "docs/de/ROADMAP.md"})
    website_pages_changed = changed & WEBSITE_PAGES

    if behavior_changed or deployment_changed:
        if "CHANGELOG.md" not in changed:
            failures.append("application or deployment changes require CHANGELOG.md")
        if not docs_en:
            failures.append("application or deployment changes require user documentation in docs/en/")
        if not docs_de:
            failures.append("application or deployment changes require matching user documentation in docs/de/")

    for page in sorted(docs_en - docs_de):
        failures.append(f"docs/en/{page} changed without docs/de/{page}")
    for page in sorted(docs_de - docs_en):
        failures.append(f"docs/de/{page} changed without docs/en/{page}")

    if website_pages_changed and website_pages_changed != WEBSITE_PAGES:
        missing = next(iter(WEBSITE_PAGES - website_pages_changed))
        failures.append(f"public website copy changed without {missing}")

    public_surface_changed = behavior_changed or deployment_changed or roadmap_changed
    if (
        public_surface_changed
        and website_pages_changed != WEBSITE_PAGES
        and not has_website_no_impact_reason(changelog_added_lines)
    ):
        failures.append(
            "public product changes require both website/index.html and "
            "website/index-en.html, or a newly added CHANGELOG.md line starting "
            f"{WEBSITE_NO_IMPACT_PREFIX!r} followed by a concrete reason"
        )

    for german_image, english_image in WEBSITE_IMAGE_PAIRS:
        if (german_image in changed) != (english_image in changed):
            missing = english_image if german_image in changed else german_image
            failures.append(f"localized website screenshot changed without {missing}")

    if deployment_changed:
        deployment_pages = {"INSTALLATION.md", "CONFIGURATION.md", "DEPLOYMENT-PROFILES.md"}
        if not docs_en.intersection(deployment_pages):
            failures.append(
                "deployment changes require INSTALLATION.md, CONFIGURATION.md or "
                "DEPLOYMENT-PROFILES.md in both languages"
            )

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Require documentation to change with user-visible application and deployment changes"
    )
    parser.add_argument("--base", required=True, help="Git revision used as the comparison base")
    args = parser.parse_args()
    changed = changed_files(args.base)
    changelog_lines = added_lines(args.base, "CHANGELOG.md") if "CHANGELOG.md" in changed else []
    failures = documentation_failures(changed, changelog_lines)
    if failures:
        raise SystemExit("Documentation change gate failed:\n- " + "\n- ".join(failures))
    print(f"Documentation change gate is valid ({len(changed)} changed files since {args.base})")


if __name__ == "__main__":
    main()
