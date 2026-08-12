# Vorrio

Vorrio is a responsive, self-hosted household inventory and shopping app.
Photograph a receipt or upload a PDF, review the recognized lines, and commit
confirmed products to your own local stock. Scan individual packages with a
phone camera, a keyboard-style hardware scanner or manual entry. Grocy can be connected as an
optional migration and export adapter, but Vorrio remains the source of truth.

The project is maintained by **Amturo UG** and licensed under
`AGPL-3.0-or-later`.

## What works in 0.8.17

- installable React PWA with a compact phone layout and a wide desktop
  workspace with persistent sidebar navigation;
- iOS-safe 16 px form controls, bounded horizontal layout, dynamic viewport
  units and safe-area-aware navigation without disabling accessible pinch zoom;
- a named first Owner, one-time family invitations, separate local accounts,
  enforced owner/admin/member/viewer roles and individually revocable browser
  sessions;
- passwordless passkey login over a stable HTTPS origin, optional TOTP for
  password login, hashed single-use recovery codes and recent-authentication
  checks before security, family or connector changes;
- scoped, expiring API tokens for Home Assistant, hand scanners and local
  services; raw values are shown once, stored only as hashes and can be revoked
  immediately without changing a human password;
- personal opt-in Web Push devices with encrypted subscriptions, a visible test
  action and non-repeating low-stock and expiry alerts;
- JPG, PNG, WebP, HEIC and multi-page PDF receipts;
- Cortecs, OpenAI, OpenRouter, Ollama, OpenAI-compatible and Anthropic adapters;
- review-before-write workflow with exact, learned and barcode matches plus a
  visible reason for every automatic match or review suggestion;
- own products, variants, barcodes, locations, units and product groups;
- local stock lots and an append-only movement journal;
- guided opening and cycle counts where blank products remain untouched, every
  entered quantity is reviewed, and differences become append-only movements;
- product-level minimum and refill targets plus a reviewed low-stock proposal
  that creates or raises open shopping-list items without duplicates;
- a responsive shared shopping screen for checking off items, adjusting
  quantities and switching between price knowledge and receipt history;
- a read-only price workspace based only on confirmed receipt imports, with
  product search, latest/lowest values, trend, historic store comparison and
  package-aware purchase history;
- a shared receipt-based household budget with an owner/admin-managed monthly
  EUR target, month-to-date spending, pace forecast, prior-month comparison,
  six-month history, store shares and explicit data-coverage diagnostics;
- a read-only Grocy stock preview that maps known products into the same count
  review without silently importing quantities or creating products;
- optional, idempotent Grocy catalog migration and one-way purchase export;
- universal Open Facts lookup for validated retail GTINs across food, beauty,
  pet food and general products, with source and license metadata; internal
  household codes remain local;
- local-first product scanning with camera, manual and keyboard-wedge input;
- immediate manual-code validation and readable structured API errors instead
  of raw technical objects;
- an on-device offline scan queue that stores only barcode, intended action and
  a stable idempotency key, then resumes resolution without changing stock;
- explicit identify, add, consume, open and shopping-list scan modes;
- a result-first mobile scan review that removes the camera after recognition,
  keeps every action visible and leaves the final confirmation within reach;
- cached external suggestions, editable product mapping and an unresolved-code
  inbox that never silently discards a scan;
- one shared product memory for receipts and scans: confirmed packages can
  resolve older open receipt lines, while fuzzy names remain review-only;
- explicit receipt-line product discovery with up to three real Open Facts
  records, including up to two image-backed options when the source provides
  them, plus store/name/brand/package evidence and optional ranking by the
  configured AI provider;
- 30-day candidate-search caching and a confirmation flow that links the real
  barcode, image and package variant to an existing or new local product;
- direct product creation and complete editing for name, image, notes,
  location, unit, group and default shelf life, with conflict detection and
  rename aliases;
- variant and barcode management with GTIN validation, duplicate protection
  and guarded deletion while receipts or stock still reference a package;
- one responsive master-data workspace for listing, creating, renaming and
  safely archiving locations, units and product groups;
- semantic duplicate-receipt detection, variant-aware receipt rows and local
  receipt-derived price history by product and store;
- idempotent scan resolution and confirmation, FIFO lot consumption and
  auditable stock movements;
- versioned REST API, Swagger UI, ReDoc and a checked-in OpenAPI 3.1 contract;
- trusted-host/proxy enforcement, origin protection, login throttling,
  security audit events, resource limits and deployment readiness checks;
- a fail-closed, explicitly acknowledged public-HTTPS profile with hardened
  CSP/HSTS/no-store responses and a repeatable external-path security smoke;
- Owner-only portable ZIP export, automatic/manual receipt-file retention,
  privacy-safe operational/audit overview and strongly confirmed complete
  installation erasure;
- an isolated launch journey plus pinned base images, image vulnerability
  scanning, CycloneDX SBOM and prepared keyless signed GHCR releases.
- a repeatable public-launch checklist for repository, package, signature,
  documentation and post-release verification.

Vorrio never accepts a fuzzy product suggestion without confirmation and never
creates a missing location, unit or group invisibly.

## Quick start

Requirements: Docker Engine with Compose v2.

```bash
cp .env.example .env
openssl rand -hex 32
```

Store the generated value as `APP_SECRET_KEY` in `.env`, then start Vorrio:

```bash
docker compose up -d --build
```

Open `http://localhost:9380`, name the first Owner, create the household password, configure an
analysis provider, and scan the first receipt or package. Live camera scanning
requires HTTPS; manual entry and hardware scanners work on a LAN HTTP address.

After the first signed public image exists, `docker-compose.release.yml` pulls
`ghcr.io/amturo/vorrio` instead of building locally. Portainer users can paste
`stack.yml`; both release templates keep data in a named Docker volume.

Never commit `.env`. The Compose templates stop with a clear error while
`APP_SECRET_KEY` is empty, and the readiness check rejects documented example
values as unsafe.

See [Installation](docs/INSTALLATION.md),
[Configuration](docs/CONFIGURATION.md) and
[Backup and restore](docs/BACKUP-RESTORE.md) for production use.

## Daily workflow

1. Photograph a receipt or upload its PDF.
2. Review names, quantities, prices and suggested products.
3. Open an uncertain line to review real image-backed candidates, choose an
   existing product or create one with visible master-data choices.
4. Commit ready lines to the local Vorrio stock.
5. If enabled and mapped, the Grocy connector mirrors the purchase afterward.

A failed optional export does not roll back a valid local stock intake. It is
reported separately and can be retried later.

For an individual package, open **Scannen**, select the intended action, scan
or type the code, review the local or Open Facts match, and confirm. No stock or
shopping data changes during lookup. Unknown codes stay in the visible review
inbox until they are mapped or deliberately discarded.

If the server or network is unavailable, an already authenticated device can
still open the cached PWA and queue package codes. Vorrio keeps at most 100
pending scans on that browser, deduplicates the same code/action pair and
requires the normal product review and confirmation after synchronization.

Under **Einstellungen → Familie & Rollen**, complete the Owner email, inspect
active browser sessions and create a 72-hour one-time invitation. The invited
person chooses an independent password; the raw invitation token is shown only
once and only its hash is stored. With more than one active user, login requires
email and password. Existing 0.8.8 browser cookies are still upgraded in place;
the migration does not change catalog, receipts or stock.

Under **Einstellungen → Konto & Sicherheit**, use the private HTTPS address to
add one or more passkeys. An authenticator app is optional. Enabling it makes
password login require a six-digit code and shows recovery codes once; store
those codes outside Vorrio. Security, family, password and connector changes
require a fresh identity confirmation after ten minutes.

Owner and Admin can create a limited automation credential in the same area
under **API-Tokens**. Choose the read-only Home Assistant preset, the scanner
preset or individual scopes, then copy the token immediately. It is not shown
again. Send it only over HTTPS in `Authorization: Bearer …`; never put it in a
URL, source file or dashboard configuration that is visible to other users.

Under **Einstellungen → Vorratsmeldungen**, enable the current HTTPS PWA device,
choose low-stock and expiry alerts and send a visible test. On iPhone or iPad,
Vorrio must first be added to the Home Screen. Alerts fire once when a condition
starts and become eligible again only after the stock or expiry condition has
returned to normal.

For an opening or shelf count, open **Vorrat → Zählen**, enter only products
that were physically checked, review every old/new quantity and confirm once.
When Grocy is connected, its balances can prefill this review; unmatched Grocy
products are listed and omitted instead of being created automatically.

For repeat purchases, open a product under **Vorrat**, set **Mindestbestand**
and **Auffüllen bis**, then use **Einkäufe → Auffüllen**. Vorrio recalculates
the shortage when you confirm, never adds the same open product twice, and
leaves products with `Auffüllen bis = 0` disabled. Scanner-added items use the
same list and can be checked off or adjusted there.

For private price knowledge, open **Einkäufe → Preise**. Vorrio compares only
prices from product lines that were reviewed and committed to stock. The view
shows the latest and lowest observation, change from the previous purchase,
historic store values and package context. These are household observations,
not live retailer prices or availability.

For household planning, open **Einkäufe → Budget**. Owner or Admin may set one
shared EUR monthly target; every account can see the confirmed spending,
remaining amount, simple calendar-pace forecast, comparable prior-month period,
history and store shares. Pending reviews, missing totals and other currencies
stay visible and do not silently enter the calculation. See
[Household budget](docs/BUDGET.md) for the exact rules and limitations.

## REST API

The canonical API is versioned under `/api/v1`.

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI 3.1: `/openapi.json`
- Health check: `/api/health`
- Deployment readiness: `/api/readiness`
- Endpoint index: [REST API](docs/API.md)

API documentation is generated from the running request and response models.
`make api-docs-check` fails when the checked-in contract is stale.
Cookie sessions remain the browser mechanism. Supported automation endpoints
also accept scoped bearer tokens; each such OpenAPI operation exposes its
required permission as `x-vorrio-required-scope`.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Installation](docs/INSTALLATION.md)
- [Deployment profiles and URLs](docs/DEPLOYMENT-PROFILES.md)
- [Configuration](docs/CONFIGURATION.md)
- [Identity and authentication](docs/IDENTITY-SECURITY.md)
- [Automation API tokens](docs/AUTOMATION-TOKENS.md)
- [Web Push notifications](docs/NOTIFICATIONS.md)
- [Household budget](docs/BUDGET.md)
- [iOS and Android plan](docs/MOBILE-APPS.md)
- [Foundation checklist](docs/FOUNDATION-CHECKLIST.md)
- [Workflow](docs/WORKFLOW.md)
- [Data model](docs/DATA-MODEL.md)
- [Product data and licenses](docs/DATA-SOURCES.md)
- [Product and barcode scanning concept](docs/BARCODE-SCANNING.md)
- [Grocy migration](docs/MIGRATION-GROCY.md)
- [Backup and restore](docs/BACKUP-RESTORE.md)
- [Data privacy, export and erasure](docs/DATA-PRIVACY.md)
- [Release and upgrade policy](docs/RELEASES.md)
- [Public launch checklist](docs/PUBLIC-LAUNCH-CHECKLIST.md)
- [AI providers](docs/AI-PROVIDERS.md)
- [Roadmap](docs/ROADMAP.md)
- [Funding](docs/FUNDING.md)
- [Governance](docs/GOVERNANCE.md)
- [Security](SECURITY.md)
- [Support](SUPPORT.md)
- [Community code of conduct](CODE_OF_CONDUCT.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Development

```bash
make api-docs
make check
```

Both commands use the project image, so contributors need Docker but no
separate host Python environment. `make check` builds the production image,
runs the backend tests, creates the frontend production bundle and rejects
stale generated API documentation.

The definition of done requires synchronized code, user documentation,
architecture, changelog and OpenAPI contract. Tests and screenshots must use
synthetic or anonymized household data.

## Public project

The planned public repository is `github.com/amturo/vorrio` and the planned
container image is `ghcr.io/amturo/vorrio`. These addresses become canonical
only after the first public release. Until then, build the image from source.

## License

Copyright (C) 2026 Amturo UG.

Vorrio is free software under the GNU Affero General Public License, version 3
or any later version. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
