# Vorrio project website

This directory contains the dependency-free, static German and English project
website. `index.html` is German and `index-en.html` is English; both link to the
other language. The site is deliberately separate from the authenticated PWA in
`frontend/` and makes no API calls.

## Preview

From the repository root:

```bash
python3 -m http.server 4173 --directory website
```

Then open `http://127.0.0.1:4173`.

The page can later be published through a static host. The canonical repository
is `https://github.com/amturo-gbr/vorrio`; it remains private during release
rehearsal. GitHub Sponsors has not yet been applied for by either the Amturo
organization or the maintainer account. The disabled Sponsors action is
intentional until the receiving organization, public wording and bookkeeping
process are ready.

`impressum.html` / `imprint.html` and `datenschutz.html` / `privacy.html` provide
the bilingual legal pages. The current static implementation uses no cookies,
browser storage, analytics or remote fonts, so no consent banner is present.
Before public deployment, replace the clearly marked hosting placeholder in
both privacy pages with the selected provider, processing agreement, retention
and transfer details, then complete a legal review.

## Design references

- `docs/design/website-hero-concept.png`
- `docs/design/website-workflow-concept.png`
- `docs/design/website-features-concept.png`
- `docs/design/website-install-support-concept.png`
- `docs/design/website-mobile-concept.png`

Product screenshots in `website/assets/` are synthetic design/QA fixtures from
the checked-in Vorrio design system. Do not replace them with private household
screenshots.

Keep localized screenshots paired: the English page uses the `*-en.png` assets,
while the German page uses the corresponding German captures. Refresh both sets
from isolated synthetic data whenever the product UI changes materially.
