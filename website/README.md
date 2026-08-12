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

The page can later be published unchanged through a static host. Before a
public deployment, confirm that the planned GitHub repository and GitHub
Sponsors profile exist, then add the legally approved Amturo imprint and
website privacy notice. The disabled Sponsors action is intentional until the
receiving account, public wording and bookkeeping process are ready.

## Design references

- `docs/design/website-hero-concept.png`
- `docs/design/website-workflow-concept.png`
- `docs/design/website-features-concept.png`
- `docs/design/website-install-support-concept.png`
- `docs/design/website-mobile-concept.png`

Product screenshots in `website/assets/` are synthetic design/QA fixtures from
the checked-in Vorrio design system. Do not replace them with private household
screenshots.
