# Contributing to Vorrio

Thank you for improving Vorrio. Keep the household workflow simple, reversible
and explicit: no silent master-data creation, no automatic acceptance of fuzzy
matches and no hidden stock changes.

## Development setup

1. Copy `.env.example` to `.env` and set a long `APP_SECRET_KEY`.
2. Run `docker compose up -d --build`.
3. Use synthetic receipts and a test provider account.
4. Run `make api-docs` after API changes.
5. Run `make check` before submitting a change.

The Make targets run the Python tooling in the project image. Docker is the
only backend development dependency required on the host. Node.js and npm are
used for the standalone frontend checks; `make check` installs the exact locked
dependencies with `npm ci`, so the gate is reproducible from a clean checkout.

## Definition of done

Every feature or behavior change must update, in the same change:

- user documentation and examples;
- `ARCHITECTURE.md` when boundaries or data flow change;
- `CHANGELOG.md`;
- request/response models and endpoint summaries;
- `docs/api/openapi.json` and `docs/en/API.md`.

Deployment, identity and mobile changes must update their threat assumptions,
supported profiles and foundation-gate documentation. A feature that weakens
the internet-exposure gate is incomplete even when its happy-path test passes.

The API documentation drift, local documentation-link and public-package
hygiene checks must pass. CI additionally compares every pull request with its
base revision: application or deployment changes are rejected unless the same
change updates `CHANGELOG.md` and paired English/German user documentation.
Deployment files specifically require installation, configuration or deployment
profile documentation. A matching, stock, migration or connector change needs
a regression test.

Public application, deployment and roadmap changes must also make an explicit
website decision. Update both `website/index.html` and `website/index-en.html`
when the public product promise changes. If the homepage is genuinely unaffected,
add a new changelog bullet in the exact form
`- Website impact: none — <concrete reason>`. The reason must describe the
unchanged public boundary; a bare "not applicable" is not sufficient. Localized
website product screenshots are pairs and must be updated together.

The public documentation has paired English and German sources in `docs/en/`
and `docs/de/`. After changing an English page, update its German counterpart
with `npm --prefix docs run translate:de:force -- --file=<PAGE>.md`, review the
wording, and run `npm --prefix docs run check`. API changes additionally require
`npm --prefix docs run translate:api:de`. The build rejects missing pages,
outdated source hashes, changed technical snippets and stale API explanations.

## Translation contributions

Start with the GitHub **New language** issue so one locale has one visible
coordination point. Generate a safe draft with:

```bash
python3 scripts/create_language_pack.py es "Español" "Spanish"
```

Language-pack pull requests use the specialized
[`language_pack.md`](.github/PULL_REQUEST_TEMPLATE/language_pack.md) template
and contain only the data-only manifest and catalog below
`language-packs/community/<locale>/`.
Run `make language-pack-check` before submission. A technically valid draft can
remain a community candidate; official status additionally requires complete
product integration, independent fluent review and Amturo maintainer approval.
Machine-assisted drafts must be disclosed and cannot review themselves. See
[Translation community](docs/en/TRANSLATION-COMMUNITY.md) for roles, status labels
and the promotion gate.

## Pull requests

- Keep one coherent behavior change per pull request.
- Explain data migration and rollback behavior.
- Include desktop and mobile screenshots for visible UI changes.
- Link the coordinating language issue and name the independent fluent reviewer
  when proposing an official language.
- Never include API keys, cookies, receipts, addresses, database exports,
  private domains, LAN addresses or personal filesystem paths.
- Add a changelog entry and mark breaking API changes clearly.

Commits should include a Developer Certificate of Origin sign-off:

```text
Signed-off-by: Your Name <you@example.com>
```

By contributing, you certify the Developer Certificate of Origin 1.1 and agree
that the contribution is licensed under `AGPL-3.0-or-later`.
