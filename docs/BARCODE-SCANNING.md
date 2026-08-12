# Product scanning

Receipt intake and package scanning solve different jobs. A receipt adds a
whole purchase efficiently; a product scan identifies one physical package for
catalog enrichment, stock correction, consumption or the shopping list.
Vorrio 0.8.14 offers both as equal primary actions backed by one local catalog.

## Entry points

- a prominent **Scannen** action in mobile and desktop navigation;
- live camera scanning on phones, tablets and camera-equipped computers;
- a focused field for USB, Bluetooth and 2.4 GHz scanners that behave like a
  keyboard and submit with Enter;
- manual code entry as an accessible fallback;
- later, the same contract behind native iOS and Android scanner plugins.

The user chooses the intended action before scanning:

| Mode | Result after confirmation |
|---|---|
| Identify | Show and, when needed, confirm product/variant metadata without changing stock quantity. |
| Add stock | Add a quantity, optional price, location and best-before date. |
| Consume | Reduce available stock through append-only movements. |
| Open | Mark an appropriate existing lot as opened. |
| Shopping list | Add or increase the unchecked item for the generic product. |

The mode is always visible and its effect is explained in plain language. On a
phone, all five actions fit without horizontal scrolling. Once a code resolves,
the acquisition panel leaves the screen, the review becomes the primary
content and the final action remains reachable above mobile navigation. Short
success/error audio feedback is used when the browser permits it.
Station-specific pinned defaults and an undo window remain future enhancements.

## Offline queue

The installed PWA can reopen its cached shell on a device that completed a
successful household login before going offline. A scan made without a server
connection stores only the normalized input code, intended action, timestamp
and one stable client mutation ID in that browser's local storage.

- no password, session cookie, catalog row, product image or receipt content is
  copied into the queue;
- no lookup, product mapping, stock movement or shopping-list change happens
  offline;
- the same barcode/action pair is queued once and the queue fails closed at 100
  entries instead of dropping an older scan;
- pending rows are visible and can be removed locally;
- reconnect or **Jetzt abgleichen** retries the original idempotent resolve
  request, then opens the normal review; confirmation remains mandatory.

An authentication failure during synchronization leaves every pending row on
the device and asks the household to sign in again. The local authenticated-
device hint unlocks only the cached shell and queue; it is not accepted by the
server as authentication.

## Resolution order

1. Preserve the raw input, normalize separators and validate supported numeric
   lengths and GTIN checksums.
2. Search `catalog_barcodes` and local variants first.
3. For checksum-valid EAN-8, UPC-A, EAN-13 and GTIN-14 values, search a fresh
   external record cached in `catalog_external_refs`.
4. Query the universal Open Facts v3 product endpoint with
   `product_type=all` when such a retail GTIN has no current local/cache result.
   Other numeric codes remain local and are never sent to an external catalog.
5. Present name, brand, quantity, image, category, product type, source and
   attribution as editable suggestions.
6. Apply no stock or shopping mutation until the user confirms the product and
   selected action.
7. After confirmation, re-evaluate unresolved receipt lines locally. Exact
   barcode, alias or name matches may resolve; fuzzy names remain suggestions.

Confirmed household values remain authoritative. External metadata fills a new
variant or an empty local field only after visible confirmation; it never
silently renames a confirmed product, moves stock or changes shelf-life.

## Known and unknown codes

A known local code shows the product, concrete variant, current stock and action
in one review panel.

An external-only result remains unresolved until the household either maps it
to an existing generic product or edits and confirms a new product/variant.
Location, unit and product group use the current local master-data lists.

An unknown code is never silently discarded. It enters **Unbekannte Codes**
with timestamp and intended mode. The household can map it, create a product or
deliberately discard the draft. Repeated unresolved scans of the same code and
mode reuse the same draft. Optional front/label photos are not part of 0.8.14.

## Camera and hardware scanners

The PWA uses `getUserMedia` in a secure context and lazy-loads the bundled
`@zxing/browser` multi-format decoder. Camera frames stay inside the browser;
only the decoded character sequence is submitted.

Live camera scanning therefore needs HTTPS (or a browser-defined localhost
exception), not a raw LAN HTTP address. When that requirement is absent, the
interface explains it and leaves manual and hardware-scanner input usable.

Keyboard-wedge scanners need no special protocol. Place the cursor in the code
field, scan, and let the scanner's Enter suffix submit. Short internal numeric
codes can be mapped locally just like retail barcodes, but deliberately skip
external product lookup. Device-specific prefixes and suffixes are not
configurable in 0.8.14.

## REST contract

The authenticated versioned resources are:

- `POST /api/v1/scans/resolve` for idempotent local/cache/external resolution;
- `GET /api/v1/scans/{scan_id}` to read one draft;
- `POST /api/v1/scans/{scan_id}/confirm` for the selected action;
- `GET /api/v1/scans/unresolved` for the review inbox;
- `PATCH /api/v1/scans/{scan_id}` to change mode, mapping or suggestion;
- `DELETE /api/v1/scans/{scan_id}` to mark an unresolved draft discarded;
- `GET /api/v1/shopping-list` to read unchecked household list items;
- `GET /api/v1/shopping-list/low-stock` to preview current refill rules;
- `POST /api/v1/shopping-list/generate` to confirm selected proposals;
- `PATCH /api/v1/shopping-list/{item_id}` to change or complete one item;
- `POST /api/v1/catalog/reconcile` to re-check open receipt lines using only
  the local catalog and learned mappings.

Resolve and confirm accept separate client-generated idempotency keys. A retry
with the same key returns the original draft/action.

Example lookup:

```http
POST /api/v1/scans/resolve
Content-Type: application/json

{
  "barcode": "4006381333931",
  "mode": "add",
  "client_mutation_id": "scan_018f3f1c8c1a"
}
```

Example confirmation for an existing local match:

```http
POST /api/v1/scans/SCAN_ID/confirm
Content-Type: application/json

{
  "client_mutation_id": "confirm_018f3f1c8c1a",
  "quantity": 2,
  "location_id": 1,
  "best_before_date": "2026-09-30"
}
```

The complete schemas, bounds and errors are generated at `/docs`, `/redoc` and
`/openapi.json`.

## Action semantics

- **Identify** changes no stock quantity.
- **Add stock** creates one lot and one positive `scan_add` movement.
- **Consume** validates total availability first and deducts from the
  earliest-expiring lots, then the oldest lots, with negative movements.
- **Open** marks the earliest appropriate unopened lot and records a zero-value
  `scan_open` movement.
- **Shopping list** reuses an unchecked item for the same product and increases
  its desired quantity. Minimum-stock generation uses that same item and never
  lowers a larger requested quantity.

## Privacy and availability

- Raw camera frames stay on the device and 0.8.14 uploads no package photos.
- When local and cached lookup miss, only a checksum-valid EAN/UPC/GTIN is sent
  to Open Facts; internal codes stay inside the installation. The result panel
  identifies every external source.
- Results are cached with provenance to reduce rate-limit pressure and make
  repeat scans fast.
- External outages fall back to a local unresolved draft rather than failing
  the complete scan workflow.
- Scanner/service accounts later receive scoped tokens instead of copied human
  browser sessions.

## Technical references

- [Open Facts universal product lookup](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/tutorials/scanning-cosmetics-pet-food-and-other-products/)
- [Open Facts v3 product endpoint](https://openfoodfacts.github.io/documentation/docs/Product-Opener/v3/products/get-api-v3-product-code/)
- [ZXing browser camera decoder](https://github.com/zxing-js/browser)
- [MDN secure-context media access](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
