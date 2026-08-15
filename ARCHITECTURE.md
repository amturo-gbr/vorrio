# Vorrio architecture

## Product boundary

Vorrio owns household products, variants, barcodes, stock, shopping data,
receipts and price history. External services enrich or receive data through
connectors; they are never the authoritative database.

Grocy remains optional for existing households:

- one-time or repeatable, idempotent catalog import into Vorrio;
- read-only balance preview for mapped products, followed by the normal Vorrio
  count review and explicit local commit;
- one-way export of reviewed purchases when a local product has a Grocy link;
- no automatic bidirectional synchronization in the 0.x series.

## Runtime

One Docker container contains:

- a React and Vite PWA;
- a FastAPI application with an OpenAPI 3.1 contract;
- one HTTPX2 client for ASGI tests and outbound provider, product-data and
  Grocy requests;
- SQLite in the persistent `/data` volume;
- optional retained receipt files below `/data/receipts`.

The public project website is a separate dependency-free static surface under
`website/`. It is not part of the authenticated application container, makes no
API request and contains no runtime configuration. A static host may publish
it independently after the public repository, legal pages and funding links
are ready. Its product media consists only of checked-in synthetic design and
QA fixtures; private installation screenshots are outside this boundary.

SQLite uses foreign keys and WAL mode. Schema changes are additive and
idempotent. A later PostgreSQL adapter must preserve the same repository and
REST contracts rather than leaking database-specific behavior into the UI.

## Localization boundary

The React PWA uses `i18next` with German source copy as the fallback key set and
a reviewed English catalog. Locale detection is local only before sign-in;
after authentication `users.preferred_locale` is authoritative per account.
The language switch updates optimistically and persists through the versioned
preferences endpoint. Server-generated personal copy (release notes, API-token
scope descriptions and Push payloads) reads that user's locale, while product
names, receipt text, currency and deployment timezone remain domain data.

Two explicit Web App Manifests keep install metadata aligned with the active
language. The static `website/` entry points are translated separately and do
not share application sessions or runtime configuration. The complete contract
and extension procedure are documented in `docs/en/LOCALIZATION.md`.

## Domain model

Generic household products and concrete sellable variants are separate:

```text
Product (Milk)
  └─ Variant (Brand, package size, image)
       └─ Barcode (EAN/UPC/GTIN)
```

Stock is represented as lots plus immutable movements. A receipt intake creates
one lot and one purchase movement for each confirmed line. Historical Grocy
product mappings are migrated into the local catalog, but historical quantities
are not guessed; current stock needs a deliberate opening count or a reviewed
Grocy balance proposal.

`stock_count_sessions` is the idempotent transaction header for a physical or
Grocy-assisted count. `stock_count_lines` preserves the previous quantity,
counted quantity, difference and selected stock context for every entered
product. Blank products are never part of a session. Positive differences add a
lot and movement; negative differences consume existing lots in FIFO order and
append one or more movements. A retry with the same client mutation identifier
returns the original session.

External product records store source, source identifier, URL, license,
attribution, payload and fetch time. External data never silently overwrites a
confirmed household value.

Package scanning adds a short-lived review aggregate above those domain
objects. `scan_drafts` records input, selected mode, resolution provenance,
suggestion and idempotency keys. Confirmation links or creates the variant and
then calls one transactional stock/list operation. The result is stored on the
draft so a retry returns the original action instead of mutating twice.

See [Data model](docs/en/DATA-MODEL.md) for table responsibilities.

## Receipt pipeline

1. Validate upload type and size.
2. Render up to four PDF pages locally and extract embedded text.
3. Send only the configured media and text to the selected provider.
4. Normalize the structured result.
5. Build a conservative semantic fingerprint and return an existing receipt
   when the same purchase was captured again.
6. Match against learned local mappings, confirmed aliases, local barcodes and
   exact names, recording explainable evidence for the chosen result.
7. Present fuzzy matches only as review suggestions. When a person opens an
   unresolved line, optionally discover real external product candidates and
   rank them without assigning one.
8. Confirming a candidate links its real barcode, image, package variant and
   provenance to the local product and learns the retailer wording.
9. Commit confirmed lines to local stock exactly once and preserve a known
   package variant for price history.
10. Optionally mirror linked lines to Grocy and report connector failures
   separately.

The source-file hash catches identical uploads before provider analysis. The
semantic fingerprint catches a second photo or PDF rendering after structured
analysis when store, date, total and at least two product lines agree.
Per-receipt locks and a unique receipt-item constraint prevent duplicate stock
intake.

## Budget read model

The budget is a derived household read model, not a second accounting ledger.
`household_budget_settings` stores only the optional integer-cent EUR target
and warning threshold. `GET /api/v1/insights/budget` aggregates receipt grand
totals at request time only when the receipt has at least one explicitly
imported line. This keeps the review-before-write boundary aligned with stock
intake and avoids treating raw OCR output as money spent.

The response contains month-to-date totals, a documented calendar-pace
forecast, the same-day prior-month window, bounded monthly history, normalized
store shares and separate coverage counts. Missing totals, pending receipts and
other currencies never enter the sum. The current one-household-per-installation
boundary is explicit; multi-household support first requires immutable
household ownership on receipts and every other domain table.

## Shared product resolution

Receipt analysis and package scanning are separate inputs to one local product
memory. Automatic receipt analysis never starts a text search. During explicit
review, opening one unresolved line may send only its normalized product wording
to the Open Facts full-text search. Store, price, brand and package context are
used locally and may be sent as structured metadata to the configured AI
provider solely to reorder real returned records. No candidate is assigned
until a person confirms it.

If a receipt contains a real barcode, the resolver checks the local variant.
The scanner may query Open Facts directly for a validated retail GTIN.
Confirming either a scan or a receipt candidate links its barcode, image,
variant and external provenance locally and immediately re-evaluates unresolved
receipt lines. Store wording and confirmed aliases work in the other direction
for future receipts.

Automatic evidence sources are exact barcode, store-specific learned wording,
an unambiguous confirmed alias and exact normalized product name. Fuzzy name
similarity is recorded as non-automatic evidence and requires review.

The scanner client has two deliberate UI states. Acquisition presents camera,
keyboard-wedge and manual input. As soon as resolution returns a draft, the
client stops the camera and replaces acquisition with a result-first review;
changing the visible action patches only that draft. The stock or shopping
mutation still happens exclusively through the idempotent confirm endpoint.
One contextual help trigger beside the active-mode summary explains all five
effects without adding nested targets to the mode tabs. It uses the shared
responsive sheet primitive, traps focus while open and performs no domain or
draft mutation.

When the server is unavailable, acquisition may instead append a bounded entry
to browser local storage. That entry contains only barcode, intended mode,
timestamp and the original resolve idempotency key. Reconnect synchronization
creates or reuses the normal server draft, removes the local entry only after a
successful response and then enters the same result-first review. Product data,
stock state and confirmation input are never synthesized offline.

## Catalog editing

The product editor changes the same local catalog used by receipt matching and
package scanning. Product updates submit the last observed `updated_at` value;
a stale form receives a conflict instead of overwriting a newer edit. Renaming
a product stores its previous normalized name as an alias so historical receipt
wording remains useful.

Sellable variants own brand, package amount/unit, image and zero or more
barcodes. Codes are normalized and validated by the scanner rules before they
are attached, and one code can belong to only one variant. A variant cannot be
deleted while a receipt, stock lot or scan draft references it.

Locations, quantity units and product groups use active/archive semantics.
Archive hides an unused entry without destroying its row. The API blocks the
operation while an active product still uses that entry and returns its current
usage count to the editor. Catalog mutations create append-only audit events;
the events contain identifiers and action names but no product notes or secret
values.

## Opening and cycle counts

The count screen reads one detailed catalog snapshot, but sends only fields a
person actually entered. The first phase supports physical counting and
optional per-line location, variant and best-before data. The second phase
shows previous, counted and difference values. Only its final confirmation
calls the transactional count endpoint.

The Grocy connector exposes stock only through a preview endpoint. Grocy rows
are aggregated defensively because installations may return one row per lot or
one row per product. Only products linked by an earlier catalog import are
proposed. Positive unmapped rows remain visible to the client and are omitted;
neither system is changed during preview. Confirming the resulting draft writes
only local Vorrio movements and does not write back to Grocy.

## Shopping-list generation

Each product may define a non-negative minimum and refill target. A target of
zero disables the rule; an enabled target must be strictly greater than the
minimum. The low-stock endpoint is a read-only projection of current lot totals
and never changes the list.

The client presents those projections for selection. Confirmation creates a
`shopping_generation_runs` header with a unique client mutation identifier,
then recalculates every selected product inside one transaction. A product is
eligible only while its current quantity remains at or below the minimum and
below the target. The desired amount is `target - current`. A missing open item
is created, while an existing one is raised only when its desired quantity is
smaller; Vorrio never lowers a person's larger request. Stale or recovered
products are recorded as skipped. `shopping_generation_items` preserves the
quantities and action used for each decision, so retries return the same run
instead of duplicating entries.

List quantity edits and completion use optimistic `updated_at` checks. Scanner
shopping mode and minimum-stock generation therefore converge on the same open
item rather than maintaining separate lists.

## Price knowledge

Price knowledge is a read-only projection of confirmed receipt intake. Both the
per-product history endpoint and the summary endpoint require `imported = 1`,
so an automatic match, fuzzy suggestion or unfinished receipt review cannot
affect a comparison. Unit price is taken from the reviewed line or derived from
its reviewed line total and quantity.

The summary groups store labels through the same retailer normalization used by
learned receipt mappings. It exposes latest, lowest and average observations,
not retailer feeds. Concrete store labels, observation dates and package
variants stay visible so clients can explain the comparison and avoid implying
live availability. The PWA reads the summary once, then loads the existing
per-product history on selection.

## API

The canonical public surface is `/api/v1`; `/api/health` and `/api/readiness`
remain unversioned for orchestrators. Pre-0.6 `/api/*` calls are rewritten
temporarily for compatibility but do not appear in the canonical OpenAPI
contract.

Browser authentication uses a signed `HttpOnly` cookie carrying a random token.
SQLite stores only the token hash in an expiring `auth_sessions` row linked to
the authenticated user and household membership. Every authenticated API dependency
resolves that row, so individual and all-other-device revocation take effect
server-side. A valid pre-0.8.9 signed household cookie is converted in place on
its first request. The OpenAPI schema declares the cookie security scheme and
complete request/response models. The generated contract and endpoint index are
committed and checked for drift.

## Security and privacy

- `APP_SECRET_KEY` encrypts provider, connector, TOTP, VAPID and browser-push
  subscription secrets at rest.
- Provider and Grocy keys never return through the public settings API.
- A visible confirmation precedes each stock-changing receipt import.
- Images can be deleted immediately after analysis or retained for a chosen
  period.
- Remote access requires HTTPS; a reverse proxy is not a replacement for the
  built-in household login.
- Explicit trusted hosts, trusted proxy networks and exact origins are separate
  controls. Login failures are throttled and security-relevant mutations are
  recorded without storing raw client IPs.
- `public_https` is a fail-closed runtime state: normal application traffic is
  unavailable until the canonical HTTPS origin, explicit host, proxy boundary,
  Secure cookie, application secret and operator acknowledgement all pass.
- Cookie-authenticated HTTPS mutations require an exact Origin; versioned API
  responses are non-cacheable and browser responses carry CSP/HSTS/opener
  isolation.
- Web Push is restricted to resolvable public HTTPS destinations. Owner-managed
  Grocy and local AI connectors deliberately retain validated private-network
  access for self-hosting.
- Request bodies, uploaded bytes, image pixels, PDF pages and PDF render sizes
  have independent limits.
- Public examples never contain real household data, LAN addresses or tokens.

The PWA uses relative same-origin API paths, so a LAN hostname and a public
hostname do not require separate frontend builds. The target deployment model
uses one canonical HTTPS hostname internally and externally. Accepted hostnames
and trusted proxy networks remain separate settings; a canonical URL never
implicitly grants network trust. See
[deployment profiles](docs/en/DEPLOYMENT-PROFILES.md).

Audit events are explicit domain objects in 0.8.3. The first named Owner,
membership role constraint and revocable browser sessions shipped in 0.8.9;
one-time invitations, separate accounts and central API permission enforcement
shipped in 0.8.10. Passkeys, encrypted optional TOTP, hashed single-use recovery
codes and recent-authentication checks shipped in 0.8.11. Scoped, expiring
bearer credentials with hash-only storage shipped in 0.8.12. Personal opt-in
Web Push with state-transition deduplication, encrypted device subscriptions
and the single-container 15-minute evaluator shipped in 0.8.13. The
receipt-based shared household budget shipped in 0.8.14 without introducing bank
data or a second ledger. Version 0.8.15 adds portable secret-free exports,
scheduled source-file retention, a minimized Owner operations/audit projection
and strongly confirmed installation erasure. Default client-address access
logs are disabled; the replacement records request ID, route template, method,
status and duration only. Version 0.8.16 completes the dedicated external-path
review and adds the enforced public runtime contract plus its production-image
smoke. Version 0.8.18 includes the shared frontend error normalizer, local manual-code
shape validation and fixed settings feedback so structured API failures remain
human-readable and visible without changing the REST contract. Remote provider
response bodies stop at the service boundary; the API returns only a bounded
status category and operator guidance. Household product photos are normalized
to metadata-free WebP, stored in the local data
volume and served only through the authenticated catalog API. Portable export
and installation erasure include this media. Browser
clients retain same-origin cookie sessions. Native clients use
browser-based Authorization Code with PKCE and revocable device tokens rather
than copying a browser cookie. See
[identity architecture](docs/en/IDENTITY-SECURITY.md) and
[mobile apps](docs/en/MOBILE-APPS.md).

Version 0.8.19 adds a small `user_experience` record per account. The REST API
returns first-run and current-release state without exposing it to automation
tokens. Completing onboarding and acknowledging a release are explicit,
idempotent writes with audit events. Existing users are migrated as introduced
to 0.8.18 and therefore see the 0.8.19 notes once; later-created accounts begin
with the product guide. The interface does not depend on browser storage, so a
phone and desktop agree on the same state.

## Product-data enrichment

Barcode lookup checks local variants first, then the Open Facts v3 endpoint with
`product_type=all`. Explicit receipt review uses the official Search-a-licious
full-text endpoint and caches each query and returned product. Results include
provenance and licensing information. Open Prices and GS1 validation are later
optional adapters; a normal EAN does not contain an expiry date.

The 0.7 scan surface provides camera, manual and keyboard-wedge inputs,
explicit action modes, cached enrichment and an unresolved-code inbox. ZXing is
loaded only when the camera starts and decodes frames locally; only the decoded
code is submitted. Camera access requires a secure HTTPS context.
See [product scanning](docs/en/BARCODE-SCANNING.md).

## Responsive client

One React application serves both form factors. Below the desktop breakpoint it
uses safe-area-aware screens and a fixed five-item bottom navigation. Wide
viewports use a persistent left sidebar, unconstrained application workspace
and feature-specific columns. Both layouts use relative same-origin API paths
and the same authenticated session and domain actions.

Mobile form controls render at a minimum of 16 CSS pixels so iOS does not zoom
and shift the visual viewport on focus. The root surfaces are horizontally
bounded, while pinch zoom remains available for accessibility. Dynamic viewport
units and safe-area insets cover browser and installed-standalone modes. A
dependency-free contract check validates those rules, manifest identity,
service-worker registration and the install icon during `make check`.

## Release boundary

`make check` runs the application contract, unit/regression tests, PWA rules,
OpenAPI drift check, guarded public-HTTPS smoke, a synthetic household launch
journey and a separate family/security acceptance journey
against temporary data.
The release-package contract operates on exactly the tracked and unignored
Git publication set. In addition to secret patterns it rejects environment,
cookie/session, browser-capture, database, build-output and local-data paths,
private IPv4 addresses, Cloudflare account endpoints and personal workstation
paths even when a contributor force-adds an otherwise ignored file.
The production container uses digest-pinned bases. CI scans it with Grype and
generates a CycloneDX SBOM. Tag releases are prepared to publish an OCI-labeled,
multi-architecture GHCR image with BuildKit provenance and a keyless Cosign
signature. Every referenced third-party Action is fixed to a full commit SHA.

## Extension boundary

The core remains AGPL. Future commercial or hosted services communicate through
documented HTTP contracts or queues. Proprietary in-process plugins are avoided
because they blur the license boundary and make self-hosted upgrades fragile.
