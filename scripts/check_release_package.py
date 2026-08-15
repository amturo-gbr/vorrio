from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = {
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/language_request.yml",
    ".github/PULL_REQUEST_TEMPLATE/language_pack.md",
    ".env.example",
    "AUTHORS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "docker-compose.release.yml",
    "stack.yml",
    "docs/API.md",
    "docs/INSTALLATION.md",
    "docs/PUBLIC-LAUNCH-CHECKLIST.md",
    "docs/STRIPE-SUPPORT.md",
    "docs/TRANSLATION-COMMUNITY.md",
    "docs/api/openapi.json",
    "frontend/src/locales/de/manifest.json",
    "frontend/src/locales/en/manifest.json",
    "language-packs/README.md",
    "language-packs/schema-v1.json",
    "scripts/create_language_pack.py",
    "scripts/check_translation_community.py",
    "website/datenschutz.html",
    "website/.vercelignore",
    "website/impressum.html",
    "website/imprint.html",
    "website/index-en.html",
    "website/index.html",
    "website/privacy.html",
    "website/support-config.js",
    "website/vercel.json",
}
FORBIDDEN_NAMES = {".env", ".DS_Store", "cookie.jar", "cookies.txt"}
FORBIDDEN_PREFIXES = (".env.",)
FORBIDDEN_PATH_PARTS = {
    ".playwright-cli",
    ".vercel",
    "__pycache__",
    "data",
    "dist",
    "node_modules",
    "output",
}
FORBIDDEN_SUFFIXES = {
    ".cookies",
    ".db",
    ".har",
    ".key",
    ".pem",
    ".session",
    ".sqlite",
    ".sqlite3",
}
TEXT_SUFFIXES = {
    "",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
FORBIDDEN_TEXT = {
    "Cloudflare API token": re.compile(r"\bcfat_[A-Za-z0-9_-]{20,}\b"),
    "Uptime Kuma API token": re.compile(r"\buk1_[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Anthropic secret": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "OpenRouter secret": re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{20,}\b"),
    "Vorrio bearer token": re.compile(r"\bvor_pat_[A-Za-z0-9_-]{32,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "credential in URL": re.compile(
        r"https?://(?!user:secret@example\.com(?:/|\b))[^\s/:]+:[^\s/@]+@"
    ),
    "hex credential assignment": re.compile(
        r"(?:access[_ -]?key|secret[_ -]?key|api[_ -]?(?:key|token))"
        r"\s*[:=]\s*[\"']?[0-9a-f]{32,64}[\"']?",
        re.IGNORECASE,
    ),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "personal macOS path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "private IPv4 address": re.compile(
        r"(?<![0-9])(?:"
        r"10(?:\.[0-9]{1,3}){3}"
        r"|192\.168(?:\.[0-9]{1,3}){2}"
        r"|172\.(?:1[6-9]|2[0-9]|3[01])(?:\.[0-9]{1,3}){2}"
        r")(?![0-9])"
    ),
    "Cloudflare account endpoint": re.compile(
        r"https://(?:api\.cloudflare\.com/client/v4/accounts/)?"
        r"[0-9a-f]{32}(?:\.r2\.cloudflarestorage\.com|(?:/|\b))",
        re.IGNORECASE,
    ),
    "generator attribution": re.compile(
        "generated "
        + r"(?:by|with)\s+(?:an?\s+)?[A-Za-z0-9_. -]{2,40}"
        + r"|\b[A-Za-z0-9_.-]+[- ]generated\s+(?:code|source|content)\b",
        re.IGNORECASE,
    ),
    "development-assistant attribution": re.compile(
        r"\b(?:"
        + "Chat"
        + r"GPT|Code"
        + "x"
        + "|Claude"
        + r"\s+Code|GitHub\s+Copilot|Cursor\s+AI)\b",
        re.IGNORECASE,
    ),
    "stale GitHub repository link": re.compile(r"github\.com/amturo/vorrio"),
    "Stripe secret key": re.compile(r"\b(?:sk|rk)_(?:test|live)_[A-Za-z0-9]{16,}"),
    "Stripe webhook secret": re.compile(r"\bwhsec_[A-Za-z0-9]{16,}"),
}
ALLOWED_TEXT_MATCHES = {
    ("backend/tests/test_app.py", "private IPv4 address"): {"192.168.1.10", "172.20.0.0"},
    ("docs/DEPLOYMENT-PROFILES.md", "private IPv4 address"): {"172.20.0.0"},
    ("docs/EXTERNAL-ACCESS-SECURITY-REVIEW.md", "private IPv4 address"): {"172.20.0.0"},
    ("scripts/check_release_package.py", "private IPv4 address"): {"192.168.1.10", "172.20.0.0"},
}


def forbidden_path_reason(path: Path) -> str | None:
    if path.name in FORBIDDEN_NAMES or (
        path.name != ".env.example" and path.name.startswith(FORBIDDEN_PREFIXES)
    ):
        return "private/generated file"
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return "private/generated file"
    if FORBIDDEN_PATH_PARTS.intersection(path.parts):
        return "private/generated path"
    return None


def forbidden_text_labels(path: Path, content: str) -> set[str]:
    labels: set[str] = set()
    rel = path.as_posix()
    for label, pattern in FORBIDDEN_TEXT.items():
        allowed_values = ALLOWED_TEXT_MATCHES.get((rel, label), set())
        for match in pattern.finditer(content):
            if match.group(0) not in allowed_values:
                labels.add(label)
                break
    return labels


def publishable_files() -> list[Path]:
    git = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if git.returncode == 0:
        listed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return [ROOT / line for line in listed.stdout.splitlines() if line]

    skipped = {".git", "node_modules", "dist", "data", "output", "__pycache__"}
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not skipped.intersection(path.relative_to(ROOT).parts)
        and path.name != ".env"
        and not path.name.endswith(".tsbuildinfo")
    )


def main() -> None:
    files = publishable_files()
    relative = {path.relative_to(ROOT).as_posix() for path in files}
    failures = [f"required public file is missing: {name}" for name in sorted(REQUIRED_FILES - relative)]

    for path in files:
        rel = path.relative_to(ROOT)
        forbidden_reason = forbidden_path_reason(rel)
        if forbidden_reason:
            failures.append(f"{forbidden_reason} would be published: {rel}")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label in sorted(forbidden_text_labels(rel, content)):
            failures.append(f"{rel}: contains {label}")

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    if not re.search(r"^APP_SECRET_KEY=$", env_example, re.MULTILINE):
        failures.append(".env.example must keep APP_SECRET_KEY empty")
    for compose_name in ("docker-compose.yml", "docker-compose.release.yml", "stack.yml"):
        compose = (ROOT / compose_name).read_text(encoding="utf-8")
        if "APP_SECRET_KEY:?" not in compose:
            failures.append(f"{compose_name}: APP_SECRET_KEY must be required")

    package_version = json.loads(
        (ROOT / "frontend/package.json").read_text(encoding="utf-8")
    )["version"]
    backend = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    backend_match = re.search(r'version="([0-9]+\.[0-9]+\.[0-9]+)"', backend)
    if not backend_match or backend_match.group(1) != package_version:
        failures.append("backend and frontend versions are not synchronized")
    if f"ghcr.io/amturo-gbr/vorrio:{package_version}" not in (
        ROOT / "stack.yml"
    ).read_text(encoding="utf-8"):
        failures.append("stack.yml does not default to the current version")

    identity_contract = {
        "AUTHORS.md": "Vorrio is developed and maintained by **Amturo UG**.",
        "NOTICE": "Copyright (C) 2026 Amturo UG",
        "README.md": "The project is maintained by **Amturo UG**",
        "frontend/package.json": '"url": "git+https://github.com/amturo-gbr/vorrio.git"',
        "backend/app/main.py": 'contact={"name": "Amturo UG"}',
    }
    for filename, marker in identity_contract.items():
        if marker not in (ROOT / filename).read_text(encoding="utf-8"):
            failures.append(f"{filename}: canonical Amturo developer identity is missing")

    history = subprocess.run(
        ["git", "log", "--all", "--format=%B"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if FORBIDDEN_TEXT["generator attribution"].search(history):
        failures.append("Git history contains generator attribution")
    if FORBIDDEN_TEXT["development-assistant attribution"].search(history):
        failures.append("Git history contains development-assistant attribution")

    vex = (ROOT / "security/vex.openvex.json").read_text(encoding="utf-8")
    for image_name in ("vorrio:ci", "vorrio:release"):
        if f'"@id": "{image_name}"' not in vex:
            failures.append(f"OpenVEX does not cover the CI image name {image_name}")

    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Public release package is clean ({len(files)} files, version {package_version})")


if __name__ == "__main__":
    main()
