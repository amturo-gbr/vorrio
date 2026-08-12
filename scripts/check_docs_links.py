from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "node_modules", "dist", "output", "__pycache__"}
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not SKIP_PARTS.intersection(path.relative_to(ROOT).parts)
    )


def local_target(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().strip("<>").split("#", 1)[0].split("?", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    decoded = unquote(target)
    if decoded.startswith("/"):
        return ROOT / decoded.lstrip("/")
    return source.parent / decoded


def main() -> None:
    failures: list[str] = []
    for source in markdown_files():
        content = source.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(content):
            target = local_target(source, match.group(1))
            if target is None:
                continue
            try:
                target.resolve().relative_to(ROOT)
            except ValueError:
                failures.append(
                    f"{source.relative_to(ROOT)}: link leaves repository: {match.group(1)}"
                )
                continue
            if not target.exists():
                failures.append(
                    f"{source.relative_to(ROOT)}: missing link target: {match.group(1)}"
                )
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Documentation links are valid ({len(markdown_files())} Markdown files)")


if __name__ == "__main__":
    main()
