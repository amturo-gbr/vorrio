from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.maintenance import rotate_secret


def main() -> int:
    data_dir = Path(os.getenv("DATA_DIR", "/data")).resolve()
    backup_path = rotate_secret(
        data_dir / "app.db",
        os.getenv("APP_SECRET_KEY", ""),
        os.getenv("APP_SECRET_KEY_NEW", ""),
    )
    print(f"Schlüsselrotation abgeschlossen. Datenbank-Sicherung: {backup_path}")
    print("APP_SECRET_KEY jetzt auf den neuen Wert setzen und Vorrio starten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
