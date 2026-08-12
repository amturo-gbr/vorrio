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
only backend development dependency required on the host; Node.js is used for
the standalone frontend production build included in `make check`.

## Definition of done

Every feature or behavior change must update, in the same change:

- user documentation and examples;
- `ARCHITECTURE.md` when boundaries or data flow change;
- `CHANGELOG.md`;
- request/response models and endpoint summaries;
- `docs/api/openapi.json` and `docs/API.md`.

Deployment, identity and mobile changes must update their threat assumptions,
supported profiles and foundation-gate documentation. A feature that weakens
the internet-exposure gate is incomplete even when its happy-path test passes.

The API documentation drift, local documentation-link and public-package
hygiene checks must pass. A matching, stock, migration or connector change
needs a regression test.

## Pull requests

- Keep one coherent behavior change per pull request.
- Explain data migration and rollback behavior.
- Include desktop and mobile screenshots for visible UI changes.
- Never include API keys, cookies, receipts, addresses, database exports,
  private domains, LAN addresses or personal filesystem paths.
- Add a changelog entry and mark breaking API changes clearly.

Commits should include a Developer Certificate of Origin sign-off:

```text
Signed-off-by: Your Name <you@example.com>
```

By contributing, you certify the Developer Certificate of Origin 1.1 and agree
that the contribution is licensed under `AGPL-3.0-or-later`.
