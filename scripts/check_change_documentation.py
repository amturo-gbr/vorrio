from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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
