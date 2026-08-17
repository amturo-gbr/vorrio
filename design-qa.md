# Design QA

## Scanner action help QA — 0.8.26

### Fidelity ledger

- **Hierarchy:** one 44 px contextual help target sits beside the existing
  active-mode explanation; the five scanner tabs retain their approved order,
  labels, icons and selected state.
- **Mobile layout:** the explanation opens as a bottom sheet at 390 × 844 px;
  all five rows and the explicit close action remain readable without
  horizontal overflow or interference from bottom navigation. The spacing
  below the action grid belongs to the complete summary row, keeping both the
  explanation and its help control visually detached from the grid.
- **Desktop layout:** the same content becomes a centered 610 px dialog while
  retaining the scanner workspace as subdued context.
- **Typography and palette:** headings, muted descriptions, borders, radii,
  Lucide strokes, green selection and primary action reuse the existing scanner
  design tokens without introducing a second visual system.
- **Interaction and accessibility:** the dialog has an accessible name and
  description, moves focus to its close control, traps Tab focus, closes via
  Escape/backdrop/explicit controls and restores focus to the trigger.
- **Copy:** German and English explain the same stock effects. The help surface
  is informational only and does not change the current mode or scan draft.

### Verification

- Compared the 390 × 844 browser render directly with
  `docs/design/scanner-entry-mobile-final-0.8.5.png`; no unintended scanner
  hierarchy, color, icon or spacing drift remained.
- Verified the centered desktop render, all five explanations, selected-mode
  emphasis, Escape closing and trigger-focus restoration in the browser.
- Full release gate passed: 73 backend tests, 15 frontend tests, bilingual i18n,
  PWA, documentation, release-package, security and OpenAPI checks.

final result: passed
