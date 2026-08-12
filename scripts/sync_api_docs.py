from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
OPENAPI_PATH = ROOT / "docs" / "api" / "openapi.json"
API_DOC_PATH = ROOT / "docs" / "API.md"


def render_api_markdown(schema: dict[str, Any]) -> str:
    rows: list[str] = []
    for path, operations in sorted(schema.get("paths", {}).items()):
        for method, operation in operations.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            tags = ", ".join(operation.get("tags", [])) or "Other"
            summary = operation.get("summary", "")
            deprecated = "yes" if operation.get("deprecated") else "no"
            rows.append(f"| `{method.upper()}` | `{path}` | {tags} | {summary} | {deprecated} |")

    return "\n".join(
        (
            "# REST API",
            "",
            "Vorrio exposes a versioned JSON API under `/api/v1`. The PWA uses the same",
            "contract as external integrations. Browser authentication uses a signed",
            "HttpOnly cookie with a random token backed by a revocable server session.",
            "",
            "- Swagger UI: `/docs`",
            "- ReDoc: `/redoc`",
            "- OpenAPI 3.1 contract: `/openapi.json`",
            "- Health check: `/api/health`",
            "- Deployment readiness: `/api/readiness`",
            "",
            "The generated contract is stored in `docs/api/openapi.json`. Run",
            "`make api-docs` after every API change and `make api-docs-check` before",
            "submitting a change.",
            "",
            "## Endpoints",
            "",
            "| Method | Path | Group | Summary | Deprecated |",
            "|---|---|---|---|---|",
            *rows,
            "",
            "## Compatibility",
            "",
            "Pre-0.6 paths below `/api` are accepted temporarily by the server, but they are",
            "not part of the canonical contract. New clients must use `/api/v1`.",
            "",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or verify Vorrio API documentation")
    parser.add_argument("--check", action="store_true", help="fail when generated files differ")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="vorrio-openapi-") as data_dir:
        os.environ.setdefault("DATA_DIR", data_dir)
        os.environ.setdefault("APP_SECRET_KEY", "openapi-generation-only-secret-key")
        sys.path.insert(0, str(BACKEND))
        from app.main import app

        schema = app.openapi()

    openapi_content = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    api_doc_content = render_api_markdown(schema)
    expected = ((OPENAPI_PATH, openapi_content), (API_DOC_PATH, api_doc_content))

    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, content in expected if not path.exists() or path.read_text() != content]
        if stale:
            print("API documentation is stale: " + ", ".join(stale))
            return 1
        print("API documentation is synchronized")
        return 0

    for path, content in expected:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"updated {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
