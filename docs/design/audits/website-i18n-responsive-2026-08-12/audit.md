# Vorrio website visual audit — 2026-08-12

## Result

The bilingual one-page website now matches the current Vorrio product UI and
remains stable at 1440 × 1000, 768 × 1024 and 390 × 844.

## Findings and fixes

1. **P1 — English page showed German product UI.** Replaced the six product
   captures with English screenshots taken from an isolated synthetic Vorrio
   household.
2. **P1 — Stock-count image was stretched and clipped.** Restored its native
   1280 × 900 aspect ratio and contained the image inside the desktop frame.
3. **P1 — Catalog phone dominated the shopping composition.** Constrained the
   phone to its 390 × 844 ratio and reduced its desktop and mobile footprint.
4. **P2 — Desktop scanner actions wrapped into an oversized layout.** Corrected
   the desktop grid override so all five actions stay on one row.
5. **P2 — Marketing images could shift while loading.** Added explicit source
   dimensions, asynchronous decoding and lazy loading below the fold.

## Verification

- 390 × 844 Playwright viewport: no horizontal overflow; zero broken images.
- German and English contract: passed; every referenced local asset resolves.
- Frontend: 12 tests passed; i18n check reports no missing, empty or suspiciously
  untranslated strings.
- Production build and bundle limit: passed.
- PWA install contract: passed.

## Evidence

- `10-en-hero-after-1440.png`
- `11-en-workflow-after-1440.png`
- `12-en-features-after-1440.png`
- `13-en-mobile-after-390.png`
- `14-en-workflow-mobile-after-390.png`
- `15-en-features-mobile-after-390.png`

final result: passed
