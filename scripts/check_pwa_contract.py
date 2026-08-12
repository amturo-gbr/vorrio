from __future__ import annotations

import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path: str, needle: str, label: str) -> None:
    content = (ROOT / path).read_text(encoding="utf-8")
    if needle not in content:
        raise SystemExit(f"PWA check failed: {label} ({path})")


def png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"PWA check failed: {path.relative_to(ROOT)} is not a PNG")
    return struct.unpack(">II", header[16:24])


def main() -> None:
    requirements = [
        ("frontend/index.html", "width=device-width, initial-scale=1, viewport-fit=cover", "accessible viewport with safe areas"),
        ("frontend/index.html", 'name="mobile-web-app-capable" content="yes"', "mobile install metadata"),
        ("frontend/index.html", 'name="apple-mobile-web-app-capable" content="yes"', "iOS install metadata"),
        ("frontend/index.html", 'name="apple-mobile-web-app-title" content="Vorrio"', "iOS app title"),
        ("frontend/index.html", 'rel="icon" type="image/png" sizes="1024x1024" href="/pwa-icon.png"', "browser favicon"),
        ("frontend/index.html", 'rel="apple-touch-icon" sizes="1024x1024" href="/pwa-icon.png"', "iOS home-screen icon"),
        ("frontend/vite.config.ts", "id: '/'", "stable manifest identity"),
        ("frontend/vite.config.ts", "display: 'standalone'", "standalone display mode"),
        ("frontend/vite.config.ts", "scope: '/'", "manifest scope"),
        ("frontend/vite.config.ts", "navigateFallback: '/index.html'", "offline navigation fallback"),
        ("frontend/vite.config.ts", "importScripts: ['/push-worker.js']", "push worker integration"),
        ("frontend/src/main.tsx", "registerSW({ immediate: true })", "service-worker registration"),
        ("frontend/public/push-worker.js", "self.addEventListener('push'", "visible Web Push handler"),
        ("frontend/public/push-worker.js", "self.addEventListener('notificationclick'", "notification click handler"),
        ("frontend/src/App.tsx", 'src="/brand/vorrio-mark.png"', "visible product brand mark"),
        ("frontend/src/styles.css", "min-height: 100dvh", "dynamic mobile viewport"),
        ("frontend/src/styles.css", "env(safe-area-inset-bottom", "safe-area navigation padding"),
        ("frontend/src/styles.css", "overflow-x: clip", "horizontal overflow guard"),
        ("frontend/src/styles.css", "font-size: 16px !important", "iOS focus-zoom prevention"),
    ]
    for path, needle, label in requirements:
        require(path, needle, label)

    index = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    blocked_zoom = ("user-scalable=no", "maximum-scale=1")
    if any(value in index for value in blocked_zoom):
        raise SystemExit("PWA check failed: pinch zoom must remain accessible")

    width, height = png_size(ROOT / "frontend/public/pwa-icon.png")
    if width != height or width < 512:
        raise SystemExit("PWA check failed: install icon must be square and at least 512px")

    for asset in ("vorrio-mark.png", "vorrio-mark-white.png"):
        mark_width, mark_height = png_size(ROOT / "frontend/public/brand" / asset)
        if mark_width != mark_height or mark_width < 512:
            raise SystemExit(
                f"PWA check failed: brand/{asset} must be square and at least 512px"
            )

    service_worker = ROOT / "frontend/dist/sw.js"
    if not service_worker.exists():
        raise SystemExit("PWA check failed: production service worker was not built")
    service_worker_content = service_worker.read_text(encoding="utf-8")
    for asset in (
        "index.html",
        "pwa-icon.png",
        "push-worker.js",
        "assets/receipt-folded.png",
        "brand/vorrio-mark.png",
        "brand/vorrio-mark-white.png",
    ):
        if service_worker_content.count(f'url:"{asset}"') != 1:
            raise SystemExit(f"PWA check failed: {asset} must occur exactly once in the precache")

    print(f"PWA contract is valid (install icon {width}x{height})")


if __name__ == "__main__":
    main()
