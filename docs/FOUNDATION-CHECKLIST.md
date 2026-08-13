# Foundation checklist

This checklist captures platform work that must not be discovered only after a
public release.

## Shipped in 0.6.1

- canonical URL, trusted-host and trusted-proxy configuration;
- Secure-cookie profiles, CSRF/origin enforcement and persistent login
  throttling by privacy-safe source fingerprint;
- request-body, image-decompression and PDF page/render limits;
- response security headers and an append-only security/API audit foundation;
- readiness diagnostics that fail closed for unsafe public settings.
- tested complete-volume backup/restore, database-integrity verification and a
  guarded offline `APP_SECRET_KEY` rotation tool.

## Shipped in 0.7.0

- explicit idempotency keys for package resolve and confirmation mutations;
- local-first package scanning with cached provenance and unresolved recovery;
- transactional stock/list actions with append-only movement records;
- responsive desktop/mobile PWA shell and secure-context camera handling;
- API-level regression coverage for retry safety and every scan action.

## Shipped in 0.7.1

- semantic duplicate-receipt detection in addition to exact upload hashes;
- explainable product-resolution evidence and review-only fuzzy candidates;
- automatic local reconciliation between confirmed scans and open receipts;
- variant-aware receipt intake and product price-history API.

## Shipped in 0.8.0

- explicit, review-only external candidate discovery with real product images;
- deterministic evidence plus constrained optional AI re-ranking;
- 30-day rate-limit-aware search caching and graceful upstream fallback;
- duplicate-safe candidate confirmation with provenance, variant and retailer
  learning;
- API and regression coverage for discovery, caching and confirmation.

## Shipped in 0.8.1

- explicit product, variant, barcode and master-data editing APIs;
- optimistic concurrency for product, variant and master-data forms;
- rename aliases, duplicate-barcode protection and guarded archive/delete
  behavior for referenced catalog data;
- catalog mutation audit events and responsive mobile/desktop editor coverage.

## Shipped in 0.8.2

- explicit opening/cycle-count review where omitted products remain untouched;
- transactional, retry-safe count sessions and append-only FIFO movements;
- read-only Grocy balance proposals with visible unmatched products and no
  automatic synchronization;
- mobile/desktop count workspace plus API regression coverage for retries and
  preview no-write behavior.

## Shipped in 0.8.3

- validated minimum/refill rules and an explicit no-write preview;
- transactional, retry-safe list generation with a fresh stock check;
- duplicate-safe convergence between scanner and generated shopping items;
- optimistic list edits, immutable generation decisions and shopping audit
  events;
- responsive list/refill/receipt-history workspace plus API regression coverage.

## Shipped in 0.8.4

- strict receipt continuation-line binding for quantity and unit-price rows;
- reviewed candidate selection that preserves up to two real product images
  when Open Facts provides them;
- regression coverage for both extraction and image-selection safeguards.
- documented private-LAN HTTPS trust for camera-enabled PWA testing without
  weakening the public-exposure gate.

## Shipped in 0.8.5

- result-first mobile scanner review with no redundant camera surface after a
  code resolves;
- all five actions visible together with an explicit mutation explanation;
- reachable mobile confirmation for long mapping and stock-detail forms;
- regression coverage that proves identify leaves stock untouched alongside
  add, consume, open and shopping-list behavior.

## Shipped in 0.8.6

- iOS-safe mobile form controls without automatic focus zoom;
- horizontal viewport containment, dynamic viewport height and safe-area
  support without blocking accessible pinch zoom;
- explicit PWA identity, scope and iOS/Android standalone metadata;
- automated PWA contract validation as part of `make check`.

## Shipped in 0.8.7

- read-only price summaries and per-product history from confirmed imports;
- normalized retailer grouping with latest, lowest and average observations;
- responsive product search, store comparison and package-aware price rows;
- explicit historic-data labeling plus regression coverage that excludes
  unresolved or merely suggested receipt lines.

## Shipped in 0.8.8

- bounded browser-local package-scan queue without offline stock mutations;
- stable mutation identifiers, duplicate suppression and retry-safe reconnect;
- visible queue review/removal plus fail-closed capacity handling;
- cached-PWA access on previously authenticated devices without persisting
  passwords, cookies, catalog data or receipt content in application storage.
- duplicate-free Workbox app-shell precaching enforced by the PWA contract.

## Shipped in 0.8.9

- additive household, first-Owner and constrained role-membership records;
- no-logout conversion of valid legacy cookies to hashed server-side session
  tokens without touching household domain data;
- 30-day per-browser sessions with privacy-safe device labels, last activity,
  individual revocation and all-other-device logout;
- responsive Owner/session management plus migration and multi-device API
  regression coverage.

## Shipped in 0.8.10

- 72-hour one-time invitations with hashed tokens and independent local
  passwords for every accepted household member;
- email plus password login when multiple users are active, with compatible
  password-only behavior for a single-user household;
- owner/admin/member/viewer permissions enforced centrally for every versioned
  API request and mirrored by role-aware PWA controls;
- member role/blocking management, immediate session revocation and replay,
  privilege-boundary and multi-user regression coverage.

## Shipped in 0.8.11

- discoverable WebAuthn passkeys bound to an exact approved HTTPS origin and
  stable relying-party hostname;
- encrypted optional TOTP with time-step replay prevention and expiring
  password-login challenges;
- hashed high-entropy single-use recovery codes, one-time display and tested
  recovery-session/password-reset flow;
- ten-minute recent-authentication checks for security, family, password,
  connector-setting and all-other-session mutations;
- responsive account-security UI, authentication audit events and complete
  migration/API regression coverage.

## Shipped in 0.8.12

- owner/admin-managed automation credentials with one-time raw display,
  SHA-256-only storage, mandatory expiry and immediate revocation;
- seven explicit least-privilege scopes for status, catalog, stock, shopping
  and scanner workflows;
- dynamic role enforcement, last-use tracking and automatic disablement when a
  creator account is blocked;
- responsive Home Assistant/scanner presets plus custom selection;
- bearer-aware OpenAPI metadata and invalid, missing-scope, expired and revoked
  credential regression coverage.

## Shipped in 0.8.13

- explicit user-gesture opt-in and secure-context enforcement for Web Push;
- encrypted VAPID private key and browser subscription material with complete
  `APP_SECRET_KEY` rotation coverage;
- personal low-stock/expiry preferences and state-transition deduplication;
- bounded delivery records, retryable transient failures and automatic 404/410
  device revocation;
- responsive PWA controls, push/click service-worker behavior and synchronized
  REST/OpenAPI/regression coverage.

## Shipped in 0.8.14

- shared owner/admin-managed monthly EUR household target with read access for
  all household roles;
- confirmed-receipt-only totals, calendar-pace forecast, comparable prior
  period, monthly history and normalized store shares;
- visible pending, missing-total, currency and coverage diagnostics rather than
  silent estimation;
- additive settings migration, privacy-safe audit events, responsive UI and
  synchronized REST/OpenAPI/regression documentation.

## Shipped in 0.8.15

- portable Owner export with manifest/checksums, optional source files and
  explicit exclusion of credentials, hashes and network fingerprints;
- previewed hourly/manual source retention constrained to `/data/receipts`;
- privacy-safe structured HTTP logs and responsive Owner operations/audit view;
- recent-authenticated, literal and double-confirmed installation erasure with
  synthetic-only destructive regression coverage;
- production-image launch journey covering catalog, barcode, receipt, stock,
  budget, export and operations;
- digest-pinned base images, fixed-vulnerability Grype gate, CycloneDX SBOM,
  full-SHA Actions pins and prepared keyless signed multi-architecture releases;
- compatible framework/crypto/runtime upgrades after a real image scan plus a
  narrow, reviewable OpenVEX statement for the unreachable CPython HTML parser.

## Shipped in 0.8.16

- a dedicated review of the browser, proxy, forwarded-header, application and
  outbound-request boundaries;
- an enforced fail-closed public runtime gate with explicit operator
  acknowledgement;
- stricter CSP/HSTS/API caching, HTTPS cookie-Origin protection and validated
  connector/push targets;
- a production-image external-path smoke included in the normal Definition of
  Done and documented residual operator responsibilities.

## Shipped in 0.8.17

- desktop and narrow-mobile UAT for every primary workspace, including long
  receipt and settings pages;
- local manual-barcode validation plus normalized structured API errors that
  remain readable for validation failures;
- fixed accessible settings feedback that does not disappear below long forms;
- a public-launch checklist covering source hygiene, CI, GHCR visibility,
  signing, SBOM, repository security settings and post-release verification;
- automated local documentation-link and publishable-package hygiene gates,
  including fail-closed secret templates and release-version consistency.

## Shipped in 0.8.18

- authenticated camera/file product images normalized to metadata-free WebP;
- local product media included in portable export and permanent erasure;
- centered wide-screen dialogs while mobile stays a bottom-sheet workflow;
- catalog onboarding copy that reflects whether Grocy is actually enabled.

## Shipped in 0.8.19

- first-login guide with one coherent receipt, scan, stock and shopping story;
- per-user completion and release acknowledgement shared across devices;
- once-per-version release notes after container updates;
- permanently accessible **Hilfe & Version** controls in Settings;
- export, erasure, audit, API and upgrade documentation for experience state.

## Shipped in 0.8.20

- an operations metric that accurately describes validation and security
  rejections without implying application failure;
- a deterministic family/security acceptance journey in the normal release
  gate, complementing the catalog/receipt/stock journey;
- immediate Owner-profile propagation into the family overview;
- clean logout/login state without stale toasts or dialogs;
- repeated desktop and narrow-mobile browser verification.

## Shipped in 0.8.21

- Starlette's maintained `httpx2` test-client path without warning suppression;
- one HTTP client for tests plus AI, product-data and Grocy requests;
- unchanged REST and persistence contracts verified by the full release gate.

## Shipped in 0.8.22

- complete German and English PWA flows, validation, API-error presentation,
  release notes and Web Push copy;
- personal persisted language selection across setup, invitations and devices;
- localized number/date/EUR formatting plus explicit preservation of household
  product, receipt, currency and timezone data;
- German and English manifests and project website entry points;
- automated translation coverage, suspicious-copy and localized backend tests.
- full-history secret scanning in CI and tag releases with a digest-pinned
  scanner plus a narrowly scoped documentation-placeholder allowlist;
- enforced Amturo UG developer identity and rejection of private artifacts and
  common credential formats;
- a fresh-runner installation proof against the private signed GHCR image;
- current npm, Python, production-image and static OWASP security reviews.

## P1 – identity hardening and automation

- optional OIDC for installations that deliberately choose an external IdP;
- signed webhooks with retries, replay protection and delivery logs;
- per-member self-service anonymization when multi-household tenancy is introduced;
- optimistic concurrency, conflict resolution and idempotency coverage for the
  remaining receipt, settings and future offline mutations;
- background job persistence for OCR, imports and notifications.

## Prepared in 0.8.23

- lazy official language chunks with a dedicated offline runtime cache;
- versioned language manifests and a central typed registry;
- a public data-only pack schema plus positive and adversarial validation tests;
- stable namespaced translation keys with a CI ceiling on legacy sentence keys;
- an explicit signature/index/compatibility gate before community packages can
  ever be installed at runtime.
- a public translation workflow with issue and pull-request templates,
  CODEOWNERS, non-destructive pack generation, truthful completion checks and
  independent fluent-review requirements.

## P1 – native-client prerequisites

- stable API compatibility and client capability discovery;
- Authorization Code with PKCE and revocable device sessions;
- offline mutation queue with deterministic deduplication;
- native push registration lifecycle and per-device notification preferences;
- Universal Links, Android App Links and passkey domain association;
- privacy declarations, accessible native flows and store demo mode.

## P2 – stable public project

- formal migration framework and downgrade/restore policy;
- PostgreSQL deployment profile without weakening SQLite support;
- accessibility testing, localization, currencies, timezones and units;
- anonymized diagnostics that are opt-in and disabled by default;
- public security contact, support policy and coordinated disclosure;
- reproducible release pipeline, changelog automation and compatibility tests;
- synthetic demo household for documentation and app-store review.
