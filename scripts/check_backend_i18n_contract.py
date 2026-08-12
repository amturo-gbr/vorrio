from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "app"
CATALOG = ROOT / "frontend" / "src" / "locales" / "en" / "translation.json"


def called_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def literal(value: ast.expr) -> str | None:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    messages: set[str] = set()

    for path in BACKEND.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                name = called_name(node.exc)
                if (
                    (name.endswith("Error") or name in {"KeyError", "RuntimeError", "ValueError"})
                    and node.exc.args
                ):
                    message = literal(node.exc.args[0])
                    if message:
                        messages.add(message)
            if isinstance(node, ast.Call) and called_name(node) == "HTTPException":
                for keyword in node.keywords:
                    if keyword.arg == "detail":
                        message = literal(keyword.value)
                        if message:
                            messages.add(message)

    missing = sorted(message for message in messages if not str(catalog.get(message, "")).strip())
    if missing:
        raise SystemExit(
            "Backend messages missing from the English catalog:\n" + "\n".join(missing)
        )
    print(f"Backend i18n contract is valid ({len(messages)} fixed messages)")


if __name__ == "__main__":
    main()
