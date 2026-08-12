# Roadmap

## 0.6 – independent foundation

- own product, variant, barcode and stock schema;
- versioned REST API and synchronized OpenAPI documentation;
- optional Grocy catalog migration and one-way export;
- Open Facts barcode lookup with attribution.

## 0.6.1 – security and deployment foundation

- documented LAN, VPN, public HTTPS and split-DNS deployment profiles;
- trusted hosts and explicit trusted-proxy networks;
- CSRF/origin enforcement, login throttling and request resource limits;
- security headers, readiness diagnostics and audit-event foundation;
- tested backup/recovery and safe secret-rotation procedures.
- documented product-camera and hardware-scanner concept, resolution order and
  unknown-barcode inbox.

## 0.7 – scanner and responsive PWA

- prominent product-scan action for PWA camera, manual entry and
  keyboard-wedge scanners;
- identify, add-stock, consume, open and shopping-list scan modes;
- local-first resolution, cached Open Facts enrichment and an unresolved-code
  review inbox;
- idempotent scan/confirm API with transactional stock/list actions;
- wide desktop sidebar/workspaces and compact safe-area-aware mobile layout.

## 0.7.1 – shared product memory

- explainable receipt matches from the shared local product catalog;
- automatic scan-to-receipt reconciliation without external text search;
- product image and concrete variant context during receipt review;
- semantic duplicate-receipt detection across different captures;
- receipt-derived product price-history REST API.

## 0.8.0 – real product candidates

- on-demand image-backed candidate discovery for unresolved receipt lines;
- store/name/brand/package evidence and constrained optional AI ranking;
- cached upstream search with license and attribution metadata;
- duplicate-safe confirmation into local products and variants.

## 0.8.1 – catalog editing

- responsive product details and editing for household defaults;
- variant and barcode management with validation and reference protection;
- complete location, unit and product-group listing, creation, rename and
  guarded archive workflow;
- optimistic concurrency and catalog audit events for every editor mutation.

## 0.8.2 – reviewed opening stock

- responsive opening and cycle-count workflow where omitted products remain
  unchanged;
- explicit old-versus-counted review with retry-safe transactional commit;
- append-only count sessions, lines and FIFO stock movements;
- read-only Grocy balance preview for mapped products, with visible unmatched
  entries and no silent creation or synchronization.

## 0.8.3 – reviewed automatic shopping list

- per-product minimum stock and refill targets in the catalog editor;
- read-only low-stock preview before any list mutation;
- selected, retry-safe generation that rechecks stock and merges open entries;
- responsive quantities, completion and receipt history under **Einkäufe**.

## 0.8.4 – receipt and image-candidate hardening

- keep printed PDF quantity/price continuation lines bound to the immediately
  preceding product, never shifted to a neighboring line;
- preserve up to two real image-backed Open Facts records in the reviewed
  three-candidate result even after optional AI ranking.

## 0.8.5 – result-first mobile scanner

- keep all five scan actions visible without a clipped horizontal strip;
- explain the selected mutation before confirmation;
- replace the acquisition surface with the product review after recognition;
- keep the final confirmation reachable throughout longer mobile forms;
- verify every action, including identify-without-stock-change, in regression
  coverage.

## 0.8.6 – mobile PWA stability

- prevent iOS focus zoom across every editable workflow;
- eliminate document-level horizontal drift down to narrow split-screen sizes;
- complete stable standalone-app identity and mobile platform metadata;
- enforce viewport, safe-area, service-worker, icon and accessibility rules in
  the automated PWA contract check.

## 0.8.7 – private price knowledge

- searchable price-history views based only on confirmed receipt imports;
- latest, lowest and previous-purchase trend per local product;
- normalized historic store comparison with package context;
- explicit distinction between household observations and live retailer data.

## 0.8.8 – safe offline scanning

- bounded on-device queue for package barcode and intended action;
- stable idempotency keys and duplicate-safe reconnect synchronization;
- cached-shell access for previously authenticated devices without caching
  passwords, sessions, catalog or receipt data;
- normal product review and explicit confirmation after every offline scan.

## 0.8.9 – owner identity and browser sessions

- additive household, user, role-membership and server-session schema;
- no-logout upgrade from the former signed household session;
- named first Owner with optional locally stored email;
- expiring per-browser sessions, device labels and immediate individual or
  all-other-device revocation;
- API, migration and multi-device regression coverage.

## 0.8.10 – family accounts and permissions

- additional local household users through expiring one-time invitations;
- independent passwords and email-based login once multiple users are active;
- owner/admin/member/viewer authorization enforced by the REST API;
- responsive member, role, blocking and invitation management;
- immediate session revocation when an account is blocked.

## 0.8.11 – passkeys and account recovery

- discoverable WebAuthn passkeys with exact HTTPS origin/RP validation;
- optional encrypted TOTP and replay-safe second-factor login;
- hashed single-use recovery codes with password-reset recovery sessions;
- recent-authentication protection for security, family and connector changes;
- responsive account-security controls and full REST/OpenAPI coverage.

## 0.8.12 – scoped automation tokens

- hash-only, expiring bearer credentials with one-time raw display;
- explicit read/write scopes for status, catalog, stock, shopping and scans;
- Home Assistant and hand-scanner presets plus custom permissions;
- immediate revocation, last-use tracking and role-aware enforcement;
- bearer-aware OpenAPI contract, audit events and boundary regression tests.

## 0.8.13 – personal stock notifications

- standards-based opt-in Web Push for installed HTTPS PWA devices;
- encrypted browser subscriptions and a locally generated encrypted VAPID key;
- personal low-stock and expiry preferences with a configurable warning window;
- state-transition deduplication, dead-device cleanup, delivery audit and a
  visible per-device test action;
- service-worker notification/click handling, responsive settings and complete
  REST/OpenAPI/regression coverage.

## 0.8.14 – receipt-based household budget

- shared optional monthly EUR target managed by Owner or Admin;
- confirmed month-to-date spending, remaining amount and transparent
  calendar-pace forecast;
- same-day prior-month comparison, six-month history and current-store shares;
- explicit pending, missing-total and non-EUR coverage diagnostics;
- responsive mobile/desktop UI plus complete REST/OpenAPI/regression coverage.

## 0.8.15 – launch readiness, privacy and release assurance

- Owner-only secret-free portable household ZIP export;
- automatic and manual source-file retention with safe path boundaries;
- privacy-safe database, failure and recent-audit operations view;
- recent-auth plus double-confirmed complete single-household erasure;
- deterministic synthetic launch journey in the normal Definition of Done;
- digest-pinned base images, Grype scan, CycloneDX SBOM, SHA-pinned Actions and
  prepared multi-architecture GHCR/Cosign releases.

## 0.8.16 – external-access security gate

- dedicated end-to-end review of browser, reverse-proxy and application trust
  boundaries;
- true fail-closed `public_https` runtime gate with an explicit final operator
  acknowledgement;
- strict canonical host/origin/proxy/cookie checks, hardened browser headers and
  no-store API responses;
- constrained connector and Web Push targets plus a production-image
  external-path regression smoke.

## 0.8.17 – release-candidate UAT and public packaging

- full desktop/mobile release-candidate walkthrough of every primary PWA
  workspace and review boundary;
- readable API-validation feedback and immediate local scanner validation;
- always-visible connection-test results on long settings pages;
- repeatable source, secret, documentation, container and GitHub/GHCR launch
  checklist.

## 0.8.18 – private product media and responsive dialogs

- camera/file product-image upload with safe WebP normalization;
- authenticated delivery, portable export and complete erasure;
- centered desktop dialogs with unchanged mobile bottom sheets;
- connector-aware catalog guidance and live non-mutating Grocy verification.

## Next family-ready PWA milestone

- optional Home Assistant webhook and dashboard cards.

External live-price comparison stays parked as a later optional connector until
a licensed, authoritative source can identify current product, package, branch,
promotion and availability without presenting household history as market data.

## 0.9 – native mobile clients

- shared Capacitor 8 workspace for iOS and Android;
- packaged local UI with configurable self-hosted HTTPS server;
- Authorization Code with PKCE and revocable device sessions;
- native camera/barcode scan, share-sheet import and secure storage;
- offline synchronization, push notifications and app links;
- TestFlight, Google Play internal testing and store privacy material.

## 1.0 – stable public release

- documented upgrade and support policy;
- PostgreSQL option for larger households;
- first public GHCR image/tag using the prepared SBOM, provenance and signing pipeline;
- accessibility, localization and full import/export audit;
- independent security-review policy and stable API compatibility policy.

The complete prioritized gate is maintained in
[Foundation checklist](FOUNDATION-CHECKLIST.md).

Recipes, chores and battery tracking are intentionally outside the initial
scope. They may become separate integrations after the inventory workflow is
excellent.
