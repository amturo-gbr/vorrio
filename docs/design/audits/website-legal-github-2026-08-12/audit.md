# Vorrio website legal and GitHub audit — 12 August 2026

## 1. Repository and ownership

- Local `origin`: `https://github.com/amturo-gbr/vorrio.git`.
- Authenticated GitHub repository: `amturo-gbr/vorrio`, private, default branch
  `main`.
- Legal project operator: Amturo UG (haftungsbeschränkt).
- The `amturo-gbr` string is an established GitHub account slug, not the current
  legal form of the operator.
- Two stale `.github/ISSUE_TEMPLATE/config.yml` links still referenced
  `amturo/vorrio`; they were corrected to `amturo-gbr/vorrio`.

## 2. GitHub launch state

- The public organization exposes zero public repositories while Vorrio remains in
  release rehearsal.
- GitHub Sponsors account settings show the same status twice: neither the
  `amturo-gbr` organization nor the `adrian-amturo` account has applied.
- No `.github/FUNDING.yml` is checked in. The website must not link to a Sponsors
  profile until the organization is accepted and payout/tax setup is complete.
- The authenticated repository page warns that the main branch is not protected.
  This is a repository launch gate and was not changed during the read-only review.

## 3. Legal implementation

- Added `impressum.html` and `imprint.html`.
- Added `datenschutz.html` and `privacy.html`.
- Used the legal identity already maintained by the Amturo company website:
  Amturo UG (haftungsbeschränkt), Eichkopfstr. 8, 65779 Kelkheim (Taunus),
  Amtsgericht Königstein im Taunus, HRB 12569, managing directors Adrian Grena
  Pérez and Michael Schairer, `info@amturo.de`, +49 155 65895162.
- Added local legal links and the full company name to both one-page footers.

## 4. Privacy and consent decision

- `website/script.js` only controls navigation, reveal states and clipboard copying.
- The marketing site loads local CSS, JavaScript, fonts via the system stack, logos
  and product images. It uses no cookies, web storage, analytics or remote embeds.
- A consent banner would have no choice to manage and is intentionally omitted.
- Production hosting is not yet selected. Both privacy pages visibly block public
  launch until hosting provider, processing agreement, retention and transfer
  details are added and legally reviewed.

## 5. Responsive and visual review

- Reference: `01-before-footer.png`.
- Result: `02-after-footer-de.png`, `03-datenschutz-de.png`, `04-privacy-en.png`.
- New legal surfaces follow the existing green/white system, brand mark, type scale,
  card radius, shell width and mobile navigation.
- A pre-existing 1280 px hero overflow was fixed by allowing the desktop grid columns
  to shrink inside the page shell. Result: 1265 px page width in a 1280 px viewport,
  no overflowing elements and no failed images after loading.

## 6. Functional verification

- German → English and English → German legal switches route to the matching page.
- Footer legal navigation routes correctly between privacy and imprint pages.
- All six static HTML pages return HTTP 200.
- Website, documentation, PWA and release-package contracts pass.
- Frontend test suite: 12 passed, 0 failed.
- Production build passes; initial JavaScript remains 421.0 KiB against a 500 KiB
  limit.

## 7. Remaining launch gates

1. Select the production host and complete both privacy hosting sections.
2. Make the audited repository public when the release gates pass.
3. Protect `main` before accepting public contributions.
4. Apply for GitHub Sponsors as the organization, finish payout/tax setup, then add
   `.github/FUNDING.yml` and activate the website button.

Overall result: passed for local pre-launch use; production privacy and GitHub launch
gates remain explicitly visible and intentionally inactive.
