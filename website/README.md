# Vorrio project website

This directory contains the dependency-free, static German and English project
website. `index.html` is German and `index-en.html` is English; both link to the
other language. The site is deliberately separate from the authenticated PWA in
`frontend/` and makes no API calls. A compact public roadmap distinguishes the
installable PWA available today from the planned native iOS and Android clients,
links to the detailed repository roadmap and routes demand through GitHub's
feature-request form.

## Preview

From the repository root:

```bash
python3 -m http.server 4173 --directory website
```

Then open `http://127.0.0.1:4173`.

The page is deployed as the static Vercel project `vorrio-website`. Its
canonical production origin is `https://vorrio.app`; `https://vorrio.de`
permanently redirects to the same path on `.app`. Both domains are assigned to
the Vercel project and verified. The canonical repository is
`https://github.com/amturo-gbr/vorrio`; it remains private during release
rehearsal. GitHub Sponsors is not shown. Stripe Payment Links are prepared as
the first funding option, but the public HTML and JavaScript contain no payment
controls or payment copy. The local `support-config.js` placeholder is excluded
from Vercel deployments. See `docs/STRIPE-SUPPORT.md` for the future activation
contract.

IONOS keeps the authoritative nameservers. Configure these apex records and
remove the existing IONOS parking `AAAA` records so IPv6 clients cannot bypass
Vercel:

| Zone | Host | Type | Value |
|---|---|---|---|
| `vorrio.app` | `@` | `A` | `216.150.1.1` |
| `vorrio.de` | `@` | `A` | `216.150.1.1` |

Vercel provisions and renews TLS automatically after DNS propagation.
`vorrio.de` is configured on the project as a permanent HTTP 308 same-path
redirect to `vorrio.app`.

`impressum.html` / `imprint.html` and `datenschutz.html` / `privacy.html` provide
the bilingual legal pages. The current static implementation uses no cookies,
browser storage, analytics, remote fonts or embedded Stripe scripts, so no
consent banner is present. Stripe is not referenced or described on the public
website until payments are deliberately activated. The privacy pages identify
Vercel as the selected host and document international-transfer safeguards.

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
