# Design QA — Vorrio logo direction 01

## Scope

- Final three-module Vorrio mark with negative-space `V`.
- Primary, inverse and 1024 px app-icon variants.
- Brand lockup in the PWA and public one-page website.

## Target comparison

The approved direction is preserved: two equal upper inventory modules, one
wide lower module and a strong negative-space `V`. The receipt-sheet symbol no
longer acts as the product brand mark.

## Render checks

- Desktop website at 1440 × 1000: mark loaded at 768 × 768 source resolution
  and rendered crisply at 34 px.
- Mobile website at 390 × 844: mark rendered at 31 px with no horizontal
  overflow (`bodyWidth === viewportWidth`).
- Dark footer: the white inverse asset loads at 768 × 768 and remains legible.
- Brand board: 48, 32 and 24 px reductions keep the module separation and `V`
  recognizable.
- All production image requests completed with non-zero natural dimensions.

## Product checks

- `npm run build`: passed.
- `npm test`: 12 passed, 0 failed.

## Notes

- Primary brand color: `#176B35`.
- The editable master artwork is retained for provenance; only cleaned
  transparent production assets are used by the app and website.

## Website QA — bilingual and responsive

### Scope

- German and English one-page website at desktop, tablet and mobile widths.
- Localized product imagery captured from an isolated synthetic Vorrio household.
- Hero, workflow, shopping/catalog composition, installation and support sections.

### Issues resolved

- English marketing pages no longer reuse German product screenshots.
- Desktop product frames preserve their 1280 × 900 source ratio, so the stock-count
  modal is no longer stretched or clipped.
- The shopping/catalog composition constrains the phone to its 390 × 844 ratio;
  it now acts as a small secondary view instead of covering the shopping screen.
- The five scanner actions remain one row on desktop instead of wrapping into an
  oversized broken control group.
- Marketing images use explicit dimensions, lazy loading where appropriate and
  asynchronous decoding to reduce layout movement.

### Responsive evidence

- Desktop: 1440 × 1000, no horizontal overflow and all nine images loaded.
- Tablet: 768 × 1024, navigation and media reflow verified.
- Mobile: 390 × 844 in Playwright, `scrollWidth === innerWidth` and zero broken images.
- Menu button, language switch, German/English navigation and localized alternative
  text were checked in the rendered pages.
- Screenshots are stored in
  `docs/design/audits/website-i18n-responsive-2026-08-12/`.

### Automated checks

- Website contract: passed (German and English, all local assets resolved).
- PWA contract: passed (install icon 1024 × 1024).
- i18n contract: 747 translated keys used, 0 missing, 0 empty and 0 suspiciously
  untranslated entries.
- Production build and bundle limit: passed (initial JavaScript 421.0 KiB / 500 KiB).

## Website QA — legal, GitHub and launch truthfulness

### Scope

- Canonical repository, current visibility and organization ownership.
- GitHub Sponsors readiness for both the organization and maintainer account.
- German and English imprint and website privacy pages.
- Cookie/banner decision against the files actually loaded by the static website.

### Verified project facts

- Git remote, repository metadata and authenticated GitHub UI all identify
  `amturo-gbr/vorrio` as the canonical repository.
- Two stale Issue-template contact links still targeted `amturo/vorrio`; both now
  use the canonical `amturo-gbr/vorrio` path.
- The repository is still private on `main`; the public organization currently has
  no public repositories.
- GitHub reports that neither `@amturo-gbr` nor `@adrian-amturo` has applied to
  GitHub Sponsors. No `.github/FUNDING.yml` is present.
- The legal operator is consistently stated as Amturo UG (haftungsbeschränkt),
  while `amturo-gbr` remains only the established GitHub organization slug.

### Changes and visual evidence

- Added German and English imprint and website privacy pages using the existing
  Vorrio brand, header, footer and responsive layout system.
- Added the legal pages to both localized footers and replaced the shortened company
  name with the full legal form.
- Reworded the disabled Sponsors action and added a factual pre-launch status instead
  of linking to an inactive sponsor profile.
- Fixed a 1280 px hero overflow uncovered during this pass; measured page width is
  now 1265 px inside a 1280 px viewport with no overflowing elements.
- Before/after footer and bilingual legal screenshots are stored in
  `docs/design/audits/website-legal-github-2026-08-12/`.

### Privacy and launch gate

- The static website makes no API calls and uses no cookies, browser storage,
  analytics, remote fonts or third-party embeds. A cookie consent banner is therefore
  intentionally absent.
- The privacy pages clearly separate the project website from independently operated
  Vorrio installations.
- Final hosting-provider, processing agreement, retention and transfer details remain
  an explicit pre-publication legal gate because no production host has been selected.

### Verification

- Website contract, documentation links, PWA contract and release package: passed.
- German and English legal navigation and language switching: passed.
- All six static HTML pages: HTTP 200.
- Frontend tests: 12 passed, 0 failed; i18n: 747 keys used, 0 missing.
- Production build and bundle limit: passed (initial JavaScript 421.0 KiB / 500 KiB).

final result: passed
