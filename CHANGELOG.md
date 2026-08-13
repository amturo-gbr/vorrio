# Changelog

## 0.8.24 – 2026-08-13

- Removed inactive Stripe controls, future-service disclosures and internal
  launch-review notes from every public website page; contribution copy now
  routes exclusively to the active GitHub workflow until payments launch.
- Synchronized the bilingual navigation, roadmap, legal pages and public
  deployment contract with the website already served at `vorrio.app`.

## 0.8.23 – 2026-08-13

- Kept the compact German safety fallback embedded and split other official
  catalogs into lazy, content-hashed chunks while retaining one Docker image
  and per-account selection.
- Added a central typed language registry with native names, text direction,
  trust tier, compatibility, capabilities and completeness metadata.
- Added a versioned data-only language-pack schema and validator that rejects
  executable/HTML content, unexpected files, unknown keys, unsafe values,
  changed placeholders and oversized catalogs, including adversarial tests.
- Added a dedicated PWA runtime cache for selected language chunks and kept
  unselected translations out of the eager offline precache.
- Began the migration to stable namespaced translation keys and added a CI
  ceiling that prevents new legacy sentence-key debt.
- Added a complete translation-community workflow with a language request form,
  specialized pull-request checklist, CODEOWNERS, lifecycle labels and explicit
  translator, fluent-reviewer and maintainer responsibilities.
- Added a non-destructive community-pack generator and CI coverage that rejects
  inaccurate community completion metadata as well as unsafe package content.
- Prepared dependency-free Stripe-hosted Payment Links for optional one-time
  and monthly project support while keeping all payment controls hidden until
  reviewed live links are explicitly configured.
- Added repeatable test-mode setup for PDF invoices and the hosted customer
  portal, then verified successful, declined, subscription-cancellation and
  refund flows without exposing Stripe credentials or test links publicly.
- Prepared the static website for Vercel with hardened response headers,
  canonical multilingual URLs, updated hosting privacy disclosures and the
  `vorrio.app` / `vorrio.de` production-domain contract.
- Added a bilingual public website roadmap that clearly separates today's
  installable PWA from the planned native iOS and Android clients and sends
  prioritization feedback to the canonical GitHub workflow.
- Enforced the website's standard `hidden` state at author level so prepared
  Stripe support controls cannot be revealed by the shared button styling.

## 0.8.22 – 2026-08-12

- Added a complete German and English PWA, including signed-out flows,
  onboarding, scanner, catalog, shopping, settings, validation and known API
  errors.
- Added a personal server-side language preference that follows each account
  across devices and is also applied to release notes, API-token scope copy and
  Web Push notifications.
- Localized number, date and EUR presentation while deliberately preserving
  product names, receipt text, stored currency and deployment timezone.
- Localized factory master data for a fresh English household and added
  explicit German and English singular/plural forms for every counted UI
  message without renaming existing household data.
- Added separate German and English install manifests plus an automated source
  audit that fails for missing translations, missing plural forms or likely
  untranslated UI copy.
- Published both German and English variants of the static project website.
- Split scanner, catalog, shopping, launch-readiness and passkey code from the
  initial JavaScript path, reducing the entry bundle from about 531 kB to
  431 kB before gzip. A release contract now prevents it from exceeding 500
  KiB unnoticed.
- Switched all repository, support, installation, signing and container
  references to the canonical `amturo-gbr/vorrio` project identity.
- Completed the English synthetic screenshot set, prevented the English
  project page from silently reusing German product views and preserved full
  screenshots without edge cropping across desktop, tablet and mobile.
- Kept all five scanner actions aligned at narrow desktop widths and added
  responsive website QA evidence for the final English launch surface.
- Replaced the network-sensitive Grype and Syft Action installers with official
  digest-pinned scanner containers, while retaining a fail-closed High/Critical
  gate and an uploaded CycloneDX CI artifact.
- Added a full-history, redacted and digest-pinned Gitleaks gate to CI and tag
  releases, expanded publishable-file credential detection and enforced Amturo
  UG as the canonical developer identity across project metadata.
- Hardened the manual published-image smoke input, added a seven-day Dependabot
  supply-chain cooldown and completed clean npm, Python, container, release-
  asset and static OWASP reviews before public visibility.

- Replaced the receipt-shaped product mark with the final Vorrio identity in
  the PWA header, desktop navigation and first-run guide, including transparent
  light/dark assets plus the new maskable app icon and browser favicon.
- Added a dependency-free, responsive bilingual project website under `website/`
  with real synthetic Vorrio product views, installation guidance, open-source
  contribution routes and an explicit pre-launch GitHub Sponsors state.
- Added coordinated desktop and mobile website concepts that extend the PWA's
  white, green and folded-receipt design system without exposing private
  installation data.
- Kept the marketing surface completely separate from the authenticated PWA
  and documented the legal, repository and receiving-account gates that remain
  before a public website or funding link goes live.

## 0.8.21 – 2026-08-12

- Made `make check` install locked frontend dependencies with `npm ci`, so CI
  and release gates work from a clean checkout without a pre-existing
  `node_modules` directory.
- Migrated Starlette's test client and Vorrio's outbound AI, product-data and
  Grocy requests from the deprecated `httpx` compatibility path to the
  maintained `httpx2` package.
- Removed the remaining non-blocking `StarletteDeprecationWarning` without
  suppressing warnings or carrying two HTTP client implementations.
- Kept the REST contract, stored household data and connector behavior
  unchanged while repeating the complete release gate.

## 0.8.20 – 2026-08-12

- Renamed the 24-hour operations metric from errors to rejected actions so
  successful validation and recent-auth security blocks are not presented as
  server failures.
- Added a deterministic family/security acceptance journey for onboarding,
  release acknowledgement, invitations, role changes, account blocking,
  passkeys, TOTP, recovery codes and password rotation.
- Refresh the family member summary immediately after the Owner changes their
  name or login email, avoiding stale "no login email" guidance.
- Clear stale success/error notices and experience dialogs on logout so a new
  login never inherits feedback from the previous session.

## 0.8.19 – 2026-08-12

- Added a responsive three-step first-login guide covering receipts, product
  scans, stock, shopping and the review-before-write safety model.
- Added per-user, server-side onboarding completion and release acknowledgement
  so the experience remains consistent across phone and desktop.
- Added clean one-time "Was ist neu?" notes after the running container version
  changes, with both the guide and current notes reopenable from Settings.
- Preserved the intended rollout for existing installations: current users see
  release notes, while accounts created after the migration receive onboarding.
- Included experience preferences in portable export, complete erasure, the
  versioned REST API, OpenAPI contract and regression coverage.

## 0.8.18 – 2026-08-12

- Added private product-photo capture and file upload from the product editor.
- Normalized household photos to bounded, metadata-free WebP in the persistent
  data volume while retaining external image addresses as an option.
- Included local product images in portable exports and complete erasure.
- Centered dialogs on desktop while preserving mobile bottom sheets.
- Removed Grocy-specific catalog guidance while the connector is disabled.

## 0.8.17 – 2026-08-12

- Completed a release-candidate UAT pass across the live desktop and mobile
  PWA, including navigation, scanner modes, catalog editing, counts, shopping,
  budget, price history, receipt review, product candidates and settings.
- Added client-side barcode shape validation so malformed manual scans receive
  an immediate German explanation without creating a failed server request.
- Normalized string, object and FastAPI validation-array error payloads so the
  interface can never render `[object Object]` as user-facing feedback.
- Moved connector and provider test results into a fixed, dismissible and
  accessible notification that stays visible on long settings pages.
- Replaced raw third-party provider error bodies with bounded guidance for
  credentials, endpoint, rate-limit and service failures.
- Expanded the frontend regression gate from the offline queue to all frontend
  unit tests and added the public-launch operator checklist.
- Added automated documentation-link and publishable-package hygiene gates,
  including version consistency, required community files, secret-pattern
  checks and fail-closed Compose application-secret templates.
- Bound the reviewed CPython HTML-parser VEX statement to both CI and release
  image names so the same High/Critical vulnerability policy is enforced
  locally and in GitHub Actions without hiding lower-severity findings.
- Replaced a substring-based budget-audit assertion with deterministic
  structured-field validation so random household identifiers cannot make CI
  fail spuriously.

## 0.8.16 – 2026-08-12

- Completed the dedicated external-access review across browser, reverse proxy,
  forwarded headers, Uvicorn, REST authentication and outbound integrations.
- Replaced the diagnostic-only public gate with a real fail-closed runtime
  boundary; incomplete `public_https` profiles now expose only health/readiness
  and return HTTP 503 for application traffic.
- Added explicit `PUBLIC_EXPOSURE_ACKNOWLEDGED`, canonical host/origin/proxy
  validation and optional Compose host-port binding without changing LAN
  defaults or publishing a route.
- Hardened CSP, opener isolation, HSTS verification, API no-store behavior and
  Origin enforcement for authenticated HTTPS cookie mutations.
- Validated Grocy/AI base URLs and constrained Web Push to resolvable public
  HTTPS destinations while retaining deliberate private-network support for
  local Owner-configured connectors.
- Added unit coverage plus a production-image external-path smoke to `make
  check`, and documented the threat model, evidence and residual operator
  responsibilities.

## 0.8.15 – 2026-08-12

- Added an Owner-only portable ZIP export with a checksummed manifest, readable
  JSON data and optional receipt sources while excluding authentication,
  connector, provider, push and network-fingerprint secrets.
- Enforced receipt-image/PDF retention automatically and on demand, including
  previews and path containment that refuses to delete outside the receipt
  directory.
- Added a responsive Owner operations/audit view with SQLite integrity, bounded
  counts and privacy-safe route-template events instead of raw request paths,
  detail payloads or IP addresses.
- Added recent-authentication and literal/double confirmation before complete
  single-household erasure; destructive tests use temporary synthetic data only.
- Added a deterministic launch smoke journey, digest-pinned base images,
  Grype image scanning, CycloneDX SBOM generation, full-SHA-pinned Actions,
  Dependabot and a prepared multi-architecture GHCR/Cosign release workflow.
- Updated FastAPI, Starlette, multipart handling, cryptography and the stable
  Python 3.14 runtime after the first image scan. Documented the sole remaining
  CPython HTML-parser match as OpenVEX `not_affected` because Vorrio has no HTML
  input or parser execution path.
- Synchronized REST/OpenAPI, security, privacy, operations, backup, release and
  upgrade documentation.

## 0.8.14 – 2026-08-12

- Added a responsive shared household-budget workspace under **Einkäufe** with
  an optional owner/admin-managed monthly EUR target.
- Added confirmed month-to-date spending, remaining amount, a transparent
  calendar-pace forecast, same-day prior-month comparison, six-month history
  and normalized current-store shares.
- Counted only receipt grand totals with at least one explicitly imported line
  and reported pending receipts, missing totals and non-EUR receipts as visible
  coverage diagnostics instead of silently mixing them into the result.
- Added additive household budget settings, role enforcement, privacy-safe
  audit events, REST/OpenAPI models, regression tests and complete operator and
  user documentation.

## 0.8.13 – 2026-08-12

- Added personal opt-in Web Push devices for the HTTPS PWA with direct-user-
  gesture permission, visible test delivery and per-device removal.
- Added low-stock and best-before preferences with a configurable 0–90 day
  window and state-transition deduplication that prevents repeated alerts until
  a condition returns to normal.
- Added encrypted browser subscriptions and an automatically generated,
  encrypted VAPID P-256 key, including complete `APP_SECRET_KEY` rotation.
- Added bounded delivery records, transient retries and automatic removal of
  404/410 push endpoints without storing message content or raw client data.
- Added the Notifications REST/OpenAPI surface, push/click service-worker
  handlers, responsive settings UI, PWA contract checks and regression tests.

## 0.8.12 – 2026-08-12

- Added owner/admin-managed API tokens for Home Assistant, hand scanners and
  local service clients with seven explicit read/write scopes and a maximum
  one-year lifetime.
- Added one-time raw-token display, SHA-256-only storage, immediate revocation,
  expiry and last-use tracking without exposing the bearer value again.
- Added `Authorization: Bearer` authentication for the documented status,
  catalog, stock, shopping-list and scanner endpoints while keeping identity,
  connector, receipt-upload and catalog-mutation endpoints session-only.
- Added responsive token presets, custom permission selection and copy-once UI
  under **Konto & Sicherheit**, plus token-aware API audit events.
- Added migration, scope-boundary, invalid/expired/revoked-token and OpenAPI
  regression coverage.

## 0.8.11 – 2026-08-12

- Added discoverable WebAuthn passkeys for passwordless login and multi-passkey
  account management, bound to an exact allowed HTTPS origin and relying-party
  hostname.
- Added optional encrypted TOTP for password login with replay prevention,
  setup QR codes and second-factor login challenges that expire after five
  minutes.
- Added ten high-entropy single-use recovery codes whose raw values are shown
  only at creation while SQLite stores only SHA-256 hashes.
- Added ten-minute recent-authentication enforcement for authenticator,
  password, Owner profile, family-role, invitation, connector-setting and
  all-other-session changes.
- Added responsive security controls, versioned REST models, audit events,
  migration coverage and complete security-flow regression tests.

## 0.8.10 – 2026-08-12

- Added 72-hour, single-use household invitations whose raw token is returned
  only at creation while SQLite stores only its SHA-256 hash.
- Added separate local passwords and email-based login for invited household
  accounts, while retaining password-only compatibility for installations with
  exactly one active user.
- Enforced owner/admin/member/viewer permissions centrally in the REST API:
  Owner controls connectors and security, Admin manages catalog and non-admin
  members, Member performs normal household mutations, and Viewer is read-only.
- Added responsive family/member management, invitation acceptance, role and
  account-state controls, role-aware navigation and read-only interface states.
- Added migration, invitation replay, multi-user login, role-boundary and
  forced-session-revocation regression coverage and synchronized OpenAPI docs.

## 0.8.9 – 2026-08-11

- Added the first explicit household, user and owner-membership records without
  changing existing catalog, receipt, stock or connector data.
- Upgraded existing signed household cookies in place to random browser tokens
  whose hashes are backed by expiring, individually revocable server sessions.
- Added a responsive **Owner & Sicherheit** workspace for the local owner name,
  optional local email, device list, individual logout and logout of all other
  devices.
- Kept first-run and existing password login compatible while preparing the
  owner/admin/member/viewer role boundary for the later invitation milestone.
- Added migration, multi-device revocation and legacy-cookie regression tests,
  synchronized OpenAPI models and explicit secret-rotation session revocation.

## 0.8.8 – 2026-08-11

- Added a bounded on-device offline scan queue for camera, manual and hardware
  scanner input, with visible pending rows, manual removal and reconnect sync.
- Reused one stable client mutation ID for every retry, deduplicated identical
  code/action pairs and failed closed at 100 entries instead of dropping data.
- Kept offline work review-only: the browser stores no product result and no
  stock/list mutation; normal server resolution and explicit confirmation are
  still required after synchronization.
- Allowed a previously authenticated device to reopen the cached PWA when the
  server is unavailable without caching the password, session cookie, catalog
  or receipt data, and added dependency-free queue regression tests.
- Removed duplicate public-asset entries from the Workbox precache and extended
  the PWA contract check to require one app-shell fallback entry per asset.

## 0.8.7 – 2026-08-11

- Added a responsive price workspace under **Einkäufe** with searchable
  products, latest/lowest values, previous-purchase trend, historic store
  comparison and package-aware purchase rows.
- Added the authenticated, read-only `/api/v1/insights/prices` endpoint with
  normalized retailer grouping and complete OpenAPI response models.
- Restricted both price summaries and product history to confirmed receipt
  lines that were actually committed to Vorrio stock; unresolved review data
  can no longer influence comparisons.
- Labeled all comparisons as historic household observations rather than live
  prices or retailer availability and added regression coverage for draft-line
  exclusion and multi-store aggregation.

## 0.8.6 – 2026-08-11

- Prevented iOS Safari from zooming and visually shifting the PWA when a scan,
  search, catalog, stock or settings field receives focus by enforcing the
  platform-safe 16 px mobile form-control size.
- Bounded the document and root surfaces against horizontal overflow, allowed
  narrow split-screen layouts below 320 px and retained accessible pinch zoom.
- Completed install metadata with a stable manifest identity/scope plus Android
  and iOS standalone-app hints.
- Added a dependency-free PWA contract check for viewport, safe areas, service
  worker registration, install icon, manifest and focus-zoom safeguards to the
  normal Definition-of-Done command.

## 0.8.5 – 2026-08-11

- Reworked the phone scanner into a result-first flow: after a code resolves,
  the camera and entry panel leave the screen and the product review moves
  directly below the selected action.
- Replaced the horizontally clipped action strip with a compact five-action
  grid and added a plain-language explanation of each action before
  confirmation.
- Kept the final action button reachable above mobile navigation while long
  product-assignment and stock-detail forms scroll underneath it.
- Added explicit regression coverage that Identify leaves stock unchanged in
  addition to the existing add, consume, open and shopping-list checks.

## 0.8.4 – 2026-08-10

- Hardened receipt analysis instructions so quantity/price continuation lines
  stay attached to the immediately preceding printed product and remain
  unresolved instead of being shifted when their position is ambiguous.
- Corrected external candidate selection so an AI ranking cannot hide every
  available product image; up to two real image-backed records remain visible
  within the three reviewed suggestions.
- Added regression coverage for both the line-binding contract and the
  image-backed candidate selection rule.
- Documented private LAN HTTPS with an explicitly trusted internal certificate
  authority for camera-enabled PWA testing.

## 0.8.3 – 2026-08-10

- Added per-product minimum stock and refill targets with validation in the
  responsive product create/edit workflow; a zero target keeps automation off.
- Added a read-only low-stock preview and an explicit selection step before
  any proposal changes the shared household shopping list.
- Added transactional, retry-safe shopping-list generation that recalculates
  stock at confirmation time, merges open product entries and never lowers an
  already larger requested quantity.
- Replaced the receipt-only purchases page with one responsive shopping area
  for list quantities, completion, refill proposals and the existing Bon
  history.
- Added versioned shopping preview/generation/update REST endpoints, immutable
  generation history, audit events, synchronized OpenAPI and workflow/data
  documentation.
- Added two end-to-end regression tests covering stale proposals, duplicate
  retries, merge behavior, optimistic item updates and authenticated API use.

## 0.8.2 – 2026-08-10

- Added a responsive opening and cycle-count workspace with search, quick
  quantity controls, optional location/variant/best-before details and an
  explicit old-versus-counted review before any stock mutation.
- Added transactional count sessions and lines, retry-safe client mutation
  identifiers, FIFO decreases, new lots for increases and an append-only audit
  trail for every confirmed difference.
- Added a read-only Grocy balance preview that aggregates lot-style responses,
  maps only previously imported products and exposes unmatched entries without
  changing Vorrio or Grocy.
- Added three versioned stock REST endpoints, synchronized OpenAPI and workflow,
  migration, architecture and data-model documentation.
- Added four regression tests for count transactions, idempotent API retries,
  Grocy preview aggregation/no-write behavior and connector stock reads.

## 0.8.1 – 2026-08-10

- Added a responsive product editor for household name, image, notes, default
  location, unit, product group and shelf life.
- Product renames now preserve the previous normalized name as a confirmed
  alias; duplicate names and stale concurrent edits return a visible conflict.
- Added variant creation/editing and guarded deletion plus barcode attach/remove
  with GTIN validation and cross-product conflict protection.
- Added a complete master-data workspace for listing, creating, renaming and
  safely archiving locations, quantity units and product groups. Usage counts
  explain why an entry cannot yet be archived.
- Added catalog audit events and three regression tests for the complete API,
  optimistic concurrency, alias preservation and reference protection.

## 0.8.0 – 2026-08-10

- Added explicit, on-demand product discovery for unresolved receipt lines with
  up to three real Open Facts records and product images.
- Added deterministic ranking from receipt wording, recognized brand, package
  quantity and retailer listings; the receipt price remains visible context and
  is never compared against an invented candidate price.
- Added optional ranking by the household's configured OpenAI-compatible,
  Anthropic or local provider. The model can only reorder supplied records and
  cannot invent products, identifiers or images.
- Added a 30-day server-side search cache that protects upstream rate limits,
  refreshes local-product links on every read and keeps repeat review fast.
- Added candidate confirmation for existing and new local products. Confirmation
  stores barcode, image, brand, package variant, provenance and learned retailer
  wording before re-evaluating other open receipt lines.
- Added responsive candidate cards, loading/fallback states, source attribution
  and a prefilled but still editable product-creation review.
- Added three regression tests for search caching/ranking, duplicate-safe local
  linking, external metadata enrichment and the complete authenticated API flow.

## 0.7.1 – 2026-08-10

- Unified receipt and package resolution around the same local product,
  variant, barcode, alias and store-mapping catalog.
- Added human-readable match evidence to receipt lines, including exact
  barcode, learned store wording, confirmed aliases, exact names and
  review-only fuzzy similarity.
- Added automatic local re-evaluation of unresolved receipt lines after a
  barcode scan or receipt mapping is confirmed, plus a manual reconciliation
  REST endpoint.
- Added conservative semantic receipt fingerprints so a differently captured
  copy of the same receipt returns the existing review instead of creating a
  second purchase.
- Added product images and concrete variant/package context to receipt review.
- Linked confirmed receipt lots to known variants and added receipt-derived
  product price history with store and package context.
- Added five regression tests for semantic deduplication, resolution evidence,
  scan-to-receipt reconciliation, variant enrichment and the expanded API.
- Added and implemented the 0.7.1 receipt-resolution design concept.

## 0.7.0 – 2026-08-10

- Added a first-class product scanner for camera, manual and keyboard-wedge
  input with identify, add-stock, consume, open and shopping-list modes.
- Added GTIN normalization and checksum validation, local-first resolution,
  30-day Open Facts caching and graceful unresolved drafts during upstream
  outages.
- Restricted external lookups to validated EAN/UPC/GTIN lengths so arbitrary
  internal scanner codes cannot be misidentified by or sent to Open Facts.
- Added an unresolved-code inbox with editable suggestions, mapping to an
  existing product, confirmed product/variant creation and deliberate discard.
- Added idempotent resolve and confirmation keys so network retries cannot
  duplicate stock or shopping-list changes.
- Added scan-created stock lots, FIFO consumption movements, opened-lot state
  and merged open shopping-list items.
- Added the complete versioned scanner REST surface and regenerated OpenAPI,
  Swagger/ReDoc models and endpoint documentation.
- Added a responsive desktop application shell with sidebar, wide workspaces
  and multi-column catalog/settings layouts while retaining the compact,
  safe-area-aware mobile PWA and five-item bottom navigation.
- Bundled ZXing as a lazy-loaded offline camera decoder; raw camera frames stay
  in the browser and live camera access fails clearly when HTTPS is absent.
- Updated the production frontend builder to Node 24 and added regression tests
  for checksum validation, all action modes, unresolved reuse and API-level
  idempotency.

## 0.6.1 – 2026-08-10

- Defined LAN, VPN, public HTTPS and combined split-DNS deployment profiles,
  including an enforced trusted-host, trusted-proxy and canonical-URL contract.
- Removed global trust in forwarded headers and added explicit proxy networks.
- Added exact origin validation for state changes, persistent login throttling,
  constant authentication failure text and privacy-safe audit events.
- Added request-body, file-size, image-pixel and PDF render limits plus security
  response headers.
- Added `/api/readiness`, which reports safe deployment diagnostics and blocks
  the unfinished direct-public profile.
- Added and tested full-volume backup/restore guidance and a guarded offline
  `APP_SECRET_KEY` rotation tool with pre-change database backup.
- Migrated universal barcode lookup from the deprecated v2 staging endpoint to
  the current Open Facts v3 production product endpoint.
- Documented the product-camera and hardware-scanner workflow, action modes,
  local-first resolution and unresolved-barcode inbox planned for 0.7.
- Added the multi-user, roles, passkey, TOTP, recovery, device-session and
  service-token security architecture.
- Selected Capacitor 8 for planned iOS and Android clients with packaged UI,
  configurable self-hosted servers and PKCE-based native authorization.
- Added a prioritized foundation checklist that blocks internet exposure until
  the required security controls are implemented and tested.

## 0.6.0 – 2026-08-10

- Made the complete quality gate reproducible with Docker-backed backend tests
  and API documentation drift checks.
- Renamed the product to Vorrio and made the local database the source of truth.
- Updated the installable PWA name and short name consistently to Vorrio.
- Added local products, variants, barcodes, master data, stock lots, movements,
  shopping-list foundation and external-source provenance.
- Added safe automatic migration of confirmed historic Grocy mappings into the
  local catalog without inventing historic stock quantities.
- Added an explicit, idempotent Grocy catalog import and made Grocy an optional
  one-way connector that can be disabled without losing configuration.
- Changed confirmed receipt intake to write local Vorrio stock first and report
  optional Grocy export failures separately.
- Added local-first barcode lookup with the universal Open Facts
  `product_type=all` API and license/attribution metadata.
- Added the Vorrat screen and changed receipt review, search and product creation
  to use the local catalog.
- Added the canonical `/api/v1` REST surface, OpenAPI 3.1 request/response
  schemas, cookie authentication declaration, Swagger UI, ReDoc and generated
  contract drift checks.
- Added public installation, configuration, migration, backup, data model,
  governance, funding and roadmap documentation with Amturo UG as maintainer.
- Preserved pre-0.6 API paths and the existing Docker volume as compatibility
  layers during migration.

## 0.5.0 – 2026-08-10

- Added the current Grocy locations, quantity units and product groups to the
  AI analysis context so the model prefers exact existing master-data names.
- Removed silent fallback to unrelated existing master data when an explicit
  AI recommendation is missing in Grocy.
- Added a review card for each missing location, unit or product group with an
  editable proposed name and an explicit create confirmation.
- Kept the complete existing Grocy lists visible in the same product form so a
  household can map to an existing value instead of creating a new one.
- Added idempotent, confirmed creation of locations, quantity units and product
  groups together with the new product. Freezer locations can be marked as such.
- Added regression coverage for AI master-data context, confirmed freezer
  creation, renamed units and case-insensitive reuse of existing groups.

## 0.4.0 – 2026-08-10

- Changed fuzzy product matches from automatic mappings to explicit amber
  review suggestions.
- Added canonical confirmed aliases that survive price, quantity and tax
  suffixes and can be reused across retailer branches.
- Added retailer, store number and address extraction.
- Added editable AI recommendations for location, unit, product group and
  default shelf-life days; concrete best-before dates are accepted only when
  printed on the receipt.
- Added OpenAI model presets while keeping custom provider model IDs possible.
- Added analysis-version-aware duplicate upload protection and per-receipt
  import serialization.
- Added migrations that demote legacy, unimported fuzzy matches safely.
- Added AGPL-3.0-or-later licensing, security, contribution, data-source and
  workflow documentation.
- Validated the release with twelve backend regression tests, a production
  Docker build, `pip check`, a PWA build and mobile/desktop visual QA.

## 0.3.2 – 2026-08-10

- Added Grocy product creation from an unresolved receipt row.
- Added Grocy launcher and imported-result state.
- Completed the first reviewed REWE purchase import.
