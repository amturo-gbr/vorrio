# Data model

## Catalog

- `catalog_products`: generic household concepts such as milk or coffee,
  including optional minimum-stock and refill-target quantities;
- `catalog_product_variants`: concrete brand and package combinations;
- `catalog_barcodes`: EAN, UPC or other codes attached to variants;
- `catalog_locations`: pantry, refrigerator, freezer and custom places;
- `catalog_quantity_units`: stock and purchase units;
- `catalog_product_groups`: household categories;
- `catalog_aliases` and `catalog_product_mappings`: confirmed receipt wording;
- `catalog_external_refs`: source, license, attribution and cached barcode or
  product-candidate metadata. Search-query cache records use a hashed context
  key and contain no provider secret.

Catalog rows keep `created_at` and `updated_at`. Product, variant and master-data
forms submit the last observed update timestamp; a stale write is rejected.
Renaming a product adds the former normalized name to `catalog_aliases` instead
of losing earlier receipt knowledge. Master data uses `active=0` as an archive,
and referenced variants remain protected from deletion.

## Stock

- `stock_lots`: current quantity, location, price, optional best-before date and
  explicit `opened_at` timestamp;
- `stock_movements`: append-only purchase, consumption, correction and transfer
  journal;
- `stock_count_sessions`: retry-safe header for a reviewed manual or
  Grocy-assisted count;
- `stock_count_lines`: immutable previous, counted and difference values plus
  selected location, variant, best-before date and created movement count;
- `shopping_list_items`: open or completed explicit future purchases;
- `shopping_generation_runs`: unique retry-safe headers for a confirmed
  minimum-stock proposal;
- `shopping_generation_items`: immutable current/minimum/target/shortage values
  and the created, updated, unchanged or skipped action per selected product.

One confirmed receipt item can create at most one stock lot. Corrections should
create movements rather than erase history. A count changes only explicitly
submitted products. Increases create a lot and movement; decreases consume
existing lots FIFO and may create several movements. The unique client mutation
identifier returns the original count session on a retry.

A refill target of zero disables automatic proposals. An enabled target must
be greater than the minimum. Generation recalculates current lot totals inside
its transaction and creates or raises an open item only while the product is
still eligible. Existing larger quantities are preserved. Completing a list
item is a checked state transition; generation history is not rewritten.

## Receipts

- `receipts`: retailer, branch, date, currency, totals, exact-file hash and
  conservative semantic receipt fingerprint;
- `receipt_items`: recognized line, confirmed product/variant link, structured
  match evidence, connector link and import state;
- `import_runs`: auditable result of each commit attempt.

## Package scans

`scan_drafts` stores the raw and normalized code, symbology, selected mode,
resolution source, optional local product/variant, external suggestion,
upstream error, status and timestamps. Resolve and confirmation keys have
partial unique indexes. A confirmed draft stores its action result so a retry
can return exactly the original response.

Known codes point directly at the existing variant. External-only and unknown
codes remain `unresolved` until a household member maps or creates a product.
Discard is a state transition rather than a history-destroying delete.

The offline package queue is deliberately not a server table. It is bounded
browser-local state containing only code, intended mode, timestamp and the
resolve idempotency key. A row reaches `scan_drafts` only after authenticated
reconnect synchronization; stock and list mutations still require a later
explicit confirmation.

## Settings, security and identities

Version 0.8.16 supports one household, separate local accounts and encrypted
connection settings. `households` identifies the tenant boundary. `users`
contains the local display name, unique optional email, independent password
hash and lifecycle flags.
`household_memberships` relates that identity to the household with a constrained
owner/admin/member/viewer role. The API enforces these memberships on every
versioned request.

`household_invitations` stores only the SHA-256 hash of a random token together
with household, inviter, recipient email/name, proposed role, expiry and
acceptance/revocation state. Acceptance creates the user and membership in one
transaction and consumes the token. The raw token is never recoverable from the
database.

`auth_sessions` contains a public session identifier, SHA-256 hash of the random
browser token, household/user links, a derived privacy-safe device label,
creation/last-seen/expiry timestamps, most recent authentication time/method and
optional revocation time. The raw token
exists only inside the signed `HttpOnly` browser cookie. No full user agent or
raw IP address is stored.

`webauthn_credentials` stores passkey public keys, signature counters, backup
state and user-chosen labels. `webauthn_challenges` binds each registration or
login attempt to a one-use challenge, exact origin, relying-party hostname and
five-minute expiry. No passkey private key enters Vorrio.

`totp_credentials` stores the shared secret encrypted with `APP_SECRET_KEY`,
enable state and last accepted time step to reject replay. `recovery_codes`
stores only SHA-256 hashes plus use timestamps. `login_challenges` holds hashed,
short-lived continuation tokens between password and second-factor checks.

`api_tokens` stores only the SHA-256 hash and non-secret prefix of each random
automation credential together with its creator, household, explicit scopes,
expiry, last-use and revocation timestamps. Raw bearer values exist only in the
one creation response.

`notification_preferences` stores each user's opt-in switch, low-stock/expiry
choices and warning window. `push_subscriptions` stores only an endpoint hash
for matching plus the full browser subscription encrypted with
`APP_SECRET_KEY`. `notification_events` records active/resolved condition
transitions so periodic checks cannot spam an unchanged state.
`notification_deliveries` keeps 90 days of non-message success/failure metadata
for retry and dead-device handling. The VAPID private key lives encrypted in
`app_settings`; only its public key is returned to authenticated browsers.

`household_budget_settings` stores one optional positive monthly limit in
integer cents, the fixed EUR currency, warning percentage, last updating user
and timestamps for the household. Removing a target deletes this setting only.
Budget summaries are derived at read time from receipt grand totals whose
receipt has at least one explicitly imported line. Pending receipts, totals at
or below zero and other currencies stay outside the sum and are returned as
coverage diagnostics. No derived monthly ledger or bank data is persisted.

`auth_attempts` stores only HMAC-fingerprinted login sources and timestamps for
throttling. `audit_events` stores category, action, outcome, a privacy-safe
source fingerprint, non-secret JSON details and creation time. The Owner
operations API projects only category, route-template action, outcome, time and
resolved local actor label; it never returns the fingerprint or detail JSON.

Multi-household access still requires explicit tenant identifiers on every
domain table before it can be enabled safely; 0.8.16 remains one household per
installation. Complete erasure clears every domain, identity, notification,
audit and setting table, removes only contained receipt source files and then
reinitializes the empty schema.

The remaining identity schema adds native device authorizations. Every catalog,
receipt, stock, shopping and settings record receives an immutable
`household_id` before multi-household access is enabled. See
[Identity and authentication](IDENTITY-SECURITY.md).

## Invariants

- external metadata cannot silently replace confirmed household data;
- fuzzy matches cannot become stock without confirmation;
- automatic receipt analysis never causes an external product-catalog search;
- an explicit candidate-review request may send only the normalized line text
  to the configured product-data source and cannot assign a product;
- a barcode belongs to one concrete variant, and exact local barcode matches
  take precedence over names;
- duplicate names, duplicate barcode ownership and stale editor writes are
  rejected transactionally;
- active product references block master-data archive, while receipt, stock or
  scan references block variant deletion;
- local stock succeeds independently of an optional connector;
- Grocy stock reads are preview-only, map only previously linked products and
  cannot mutate local stock before count confirmation;
- omitted count products remain unchanged and a repeated client mutation
  identifier cannot apply a difference twice;
- low-stock preview is read-only, generation rechecks every selected product,
  and one client mutation identifier cannot duplicate list entries;
- generated shortages may raise but never lower an existing open request;
- budget settings never alter receipt or stock history, and only explicitly
  committed receipt totals can enter a budget sum;
- destructive history rewrites are avoided;
- migrations are additive and idempotent.

The scanner uses unresolved scan drafts and idempotent client mutation
identifiers together with existing barcode, external-reference, stock movement
and shopping-list tables. See [Product scanning](BARCODE-SCANNING.md).
