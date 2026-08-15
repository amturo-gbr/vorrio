# Household workflow

## Accounts, family and devices

New installations name the first Owner while setting the household password.
After an upgrade, the existing password and logged-in browser keep working; the
highlighted **Einstellungen → Owner & Sicherheit** card completes the local
display name and optional email without changing household data.

Every login creates a separate 30-day server-side browser session. The settings
card lists a privacy-safe browser/device label and last activity. One row can be
revoked immediately, or **Andere Geräte abmelden** can keep only the current
browser. Revoking the current row returns to login.

Before inviting someone, Owner saves a unique local email. Under **Konto &
Familie**, Owner or Admin enters a name, email and allowed role. The resulting
link expires after 72 hours and works once; the recipient chooses an independent
password. Admin cannot grant Admin or change Owner/Admin accounts. Blocking an
account logs it out on the next request. With multiple active users, everyone
logs in with email plus password. Recovery and MFA remain later milestones.

## Receipt intake

1. Photograph a receipt or upload an image/PDF.
2. Vorrio extracts retailer, date, lines, quantities and prices.
3. Learned wording, confirmed aliases, local barcodes and exact local product
   names match automatically with a visible explanation.
4. Fuzzy suggestions remain amber until confirmed. Opening one unresolved line
   explicitly searches for up to three real, image-backed product candidates.
5. Vorrio ranks candidates by name, brand, package and retailer evidence. If a
   provider is configured, it may reorder only those real records; it cannot
   create another product or image.
6. Selecting a known candidate links it to the existing local product. A new
   candidate opens an editable form with the full existing location,
   unit and product-group lists.
7. Confirmation stores its barcode, image and package variant and learns the
   wording for that retailer. The same choice can resolve other open lines.
8. Confirmed lines are committed once to local stock.
9. An enabled Grocy connector may mirror linked lines afterward.

Connector failure never removes a successful local intake. It is displayed as
a separate retryable result.

## Product and variant

Use a generic product for the household concept, such as “Milk”. A concrete
brand, package size and barcode belongs to a variant. Multiple variants can
share one stock and shopping concept.

A product image can come from a confirmed external product record, an optional
HTTP(S) address or a household camera/file upload. Local uploads accept JPEG,
PNG and WebP, are oriented, reduced to at most 1600 pixels per edge and stored
as metadata-free WebP. They are served only through the authenticated API. The
catalog mentions Grocy as an onboarding option only while that connector is
enabled; Vorrio otherwise remains fully standalone.

Receipt intake does not require a barcode. Scan a package later to enrich or
create its variant. Once confirmed, Vorrio re-checks unresolved older receipt
lines and can connect an exact barcode or now-known product automatically.
Local matches are checked before external Open Facts data.

Product discovery runs only after a person opens a specific receipt line. Open
Facts receives the normalized product wording, not the complete receipt image,
address or payment data. The configured AI provider receives only the line and
candidate metadata needed for ranking. Search results are cached for 30 days.

Responsive implementation references:

- [mobile product candidates](design/product-candidates-mobile-final-0.8.0.png)
- [desktop product candidates](design/product-candidates-desktop-final-0.8.0.png)

The product scanner is a separate primary workflow with identify, add,
consume, open and shopping-list modes. It supports phone cameras over HTTPS,
manual entry and scanners that behave like a keyboard. Unknown codes remain in
a review inbox instead of being lost. See [Product scanning](BARCODE-SCANNING.md).

Manual input rejects anything other than 4–18 digits, with spaces and hyphens
allowed only as separators, before contacting the server. Checksum and conflict
validation still runs authoritatively on the API. Structured API validation
details are converted into readable field messages; raw objects are never
shown to the household.

## Catalog editing

1. Open **Vorrat** and select a product.
2. Edit the household name, image, notes, default location, unit, product group
   or shelf life. Saving keeps the old product name as a matching alias.
3. Add or open a concrete variant to maintain brand, package size, image and
   barcodes. A validated barcode can belong to only one variant.
4. A variant with receipt, stock or scan references stays protected. Remove or
   correct the referencing workflow instead of deleting history.
5. Open **Stammdaten** to see every location, unit and group with its product
   usage count. Entries may be added or renamed immediately.
6. Archive is available only when no active product still uses the entry. The
   editor explains which reassignment is required first.

If another browser saved the same record after the form was opened, Vorrio
rejects the stale save and asks for a reload rather than overwriting it.

Responsive implementation references:

- [mobile product editor](design/catalog-editor-mobile-final-0.8.1.png)
- [desktop product editor](design/catalog-editor-desktop-final-0.8.1.png)
- [mobile master-data editor](design/master-data-editor-mobile-final-0.8.1.png)
- [desktop master-data editor](design/master-data-editor-desktop-final-0.8.1.png)

## Opening and cycle count

1. Open **Vorrat → Zählen**. Every quantity field starts blank; blank products
   are outside the transaction and remain unchanged.
2. Search by product or location and enter the physically counted quantity.
   Plus/minus controls start from the currently recorded stock. Expand a line
   only when location, concrete variant or best-before date needs adjustment.
3. If Grocy is enabled, **Grocy-Vorschlag** reads its current balances and
   prefills only already mapped Vorrio products. Unmapped positive Grocy rows
   are reported and omitted. Preview changes neither application.
4. Select **Änderungen prüfen**. Compare every previous and counted quantity;
   zero differences remain visible but create no movement.
5. Confirm once. Vorrio creates one immutable count session, its lines and the
   required append-only stock movements. Network retries reuse the same client
   mutation identifier and return the original result.
6. The result reports entered and changed products. Positive differences create
   a lot; negative differences consume the earliest-expiring available lots
   first.

The flow is suitable for an initial inventory, one shelf or a later correction.
It is not an automatic Grocy synchronization and never creates a missing
product or master-data entry.

Responsive implementation references:

- [mobile count entry](design/stock-count-mobile-final-0.8.2.png)
- [mobile count review](design/stock-count-review-mobile-final-0.8.2.png)
- [desktop count entry](design/stock-count-desktop-final-0.8.2.png)
- [desktop count review](design/stock-count-review-desktop-final-0.8.2.png)

## Minimum stock and shopping list

1. Open a product under **Vorrat** and set **Mindestbestand** plus
   **Auffüllen bis**. The target must be greater than the minimum; target `0`
   keeps the rule disabled.
2. Open **Einkäufe → Liste**. A green **Auffüllen** card appears only when an
   eligible product is not already represented with at least the calculated
   shortage.
3. Review every proposal. Vorrio shows current, minimum, target and exact
   proposed quantity. Deselect anything that should wait.
4. Confirm once. The server rechecks current stock transactionally, skips a
   now-recovered product and returns the original generation result on a retry.
5. An existing unchecked item is raised only if the new shortage is larger;
   it is never duplicated or reduced. Scanner shopping mode uses the same item.
6. Adjust quantities with plus/minus and check an item off in the shared list.
   Optimistic timestamps prevent a stale browser from overwriting a newer edit.
7. Switch to **Bon-Verlauf** in the same screen for all processed receipts.

The rule creates suggestions, not unattended purchases. Stock changes still
come from reviewed receipts, package actions or a count; checking an item off
does not invent stock.

Responsive implementation references:

- [mobile shopping list](design/shopping-list-mobile-final-0.8.3.png)
- [mobile refill review](design/shopping-refill-mobile-final-0.8.3.png)
- [desktop shopping list](design/shopping-list-desktop-final-0.8.3.png)
- [desktop refill review](design/shopping-refill-desktop-final-0.8.3.png)

## Package scan

1. Open **Scannen** and select the intended action before capturing the code.
2. Use the HTTPS camera, enter the digits, or scan into the focused field with
   a USB, Bluetooth or 2.4 GHz keyboard-wedge scanner.
3. If the server is unavailable, Vorrio keeps only code, intended action,
   timestamp and one stable idempotency key in the visible on-device queue. It
   makes no product, stock or list decision offline.
4. After reconnect or **Jetzt abgleichen**, Vorrio validates the code and checks the local variant first, then its
   external cache and Open Facts.
5. After recognition, the camera panel closes and the review moves to the top.
   The selected action and its exact effect remain visible. **Aktionen erklärt**
   opens one overview of all five modes without changing the current selection.
6. Review the product and source. Map an external or unknown result to an
   existing product, or edit the proposed name and create it deliberately.
7. Add quantity, location, date or price only when the selected action needs
   those values, then confirm once.
8. A repeated network request with the same idempotency key returns the first
   result instead of creating another lot or movement.
9. Vorrio re-evaluates open receipt lines against the newly confirmed local
   barcode and product. Exact hits are assigned; fuzzy hits stay suggestions.

Add creates a new lot and movement. Consume removes from the earliest-expiring
available lots first. Open marks the earliest suitable unopened lot. Shopping
list reuses an existing unchecked item for the same product and increases its
desired quantity. Identify changes no stock quantity.

Responsive implementation references:

- [mobile scanner entry](design/scanner-entry-mobile-final-0.8.5.png)
- [mobile result-first review](design/scanner-review-mobile-final-0.8.5.png)

## Master data suggestions

Vorrio compares each proposed location, unit and product group against the full
local list. An exact value is selected. A missing value stays editable and must
be confirmed before creation. Similar but semantically wrong entries are not
chosen just to avoid creating a new value.

## Prices and receipt-only lines

Deposits, discounts and other non-stock lines remain outside inventory. The
review shows receipt total, product value and the difference. Confirmed product
lines preserve store, unit price, purchase date and a known package variant for
the product price-history API.

Open **Einkäufe → Preise** to use those confirmed observations. The overview
groups branches by normalized retailer, while keeping the concrete observed
store label and date visible. Selecting a product shows its latest and lowest
price, change from the previous confirmed purchase, per-store latest/lowest
values and the package-aware history. Draft, unresolved and merely suggested
receipt lines are excluded. A result describes household history only; it is
not a live price, promotion or availability claim.

## Household budget

1. Open **Einkäufe → Budget**. Every household role can read the same overview.
2. Owner or Admin may choose **Anpassen**, set a monthly EUR target and select
   the 70, 80, 90 or 100 percent warning point. Vorrio never invents a target.
3. Review the confirmed month-to-date amount, remaining target and the simple
   calendar-pace forecast. The forecast extrapolates elapsed calendar days and
   is an orientation rather than a prediction.
4. Compare only the same elapsed-day window of the prior month. Six-month bars
   and current-store shares use the same counting rule.
5. Check the data note before acting: a pending receipt, missing total or
   non-EUR total remains visible but excluded. Resolve the receipt in the normal
   review workflow; the next overview request recalculates automatically.
6. Removing a target keeps every receipt and historic summary. The view then
   remains useful as a receipt-derived spending overview.

A receipt enters the sum only after at least one of its lines was explicitly
committed to Vorrio stock. Merely uploading or analyzing a receipt cannot alter
the budget. The feature neither connects a bank nor claims current retailer
prices.

## Duplicate receipts

Identical file bytes are rejected before a paid provider call. A second photo
or differently rendered PDF can only be recognized after analysis; Vorrio then
compares store, date, total and a sorted signature of at least two product
lines. A match returns the existing review with `duplicate=true` and discards
the new temporary upload.

## Grocy transition

Use “Katalog übernehmen” to copy products and master data safely into Vorrio.
The import is repeatable. See [Grocy migration](MIGRATION-GROCY.md).
