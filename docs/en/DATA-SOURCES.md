# Product, barcode and price data

No single database reliably combines every retailer, private-label product,
barcode, image, price and expiry date. Vorrio keeps confirmed household data as
the authority and records provenance for every external value.

## Open Facts

Barcode lookup uses the current Open Facts v3 product endpoint with
`product_type=all`. One request can resolve food, beauty, pet-food and general
product records and may follow a redirect to the matching Open Facts project.
Explicit receipt review uses the official Search-a-licious full-text API for
real food-product candidates.

Useful fields include product name, brand, image, package quantity, category and
product type. Coverage is community-maintained and may be incomplete or wrong.
Vorrio therefore treats a result as a suggestion until the household confirms
it.

The package scanner consults Open Facts only for a checksum-valid retail GTIN.
The receipt workflow never searches during automatic analysis. When a person
opens an unresolved line, Vorrio may send only its normalized product wording
to full-text search and display at most three records. Retailer, brand, package
and receipt-price context are evaluated locally; the price is not treated as a
candidate price when the source provides none. After confirmation, barcode,
image, brand, package data and retailer wording become local.

Database content is reused under ODbL. Product images can require CC BY-SA
attribution. Vorrio stores source URL, database license, image license,
attribution and fetch time with imported metadata.

Open Facts limits individual product reads and allows at most ten search
requests per minute and source IP. Vorrio therefore queries only checksum-valid
EAN-8, UPC-A, EAN-13 and GTIN-14 values during scanning, starts text search only
from an explicit receipt-line review, caches both paths for 30 days and never
uses remote search as type-ahead. Internal numeric codes remain local. See
[Product scanning](BARCODE-SCANNING.md).

Search-a-licious coverage and retailer tags are community-maintained. A missing
store tag means “unknown”, not “unavailable at this retailer”. Store context is
therefore a ranking hint rather than an exclusion filter.

## Open Prices

Open Prices can provide community observations tied to products and locations.
It is planned as an optional comparison layer, not as the authority for the
household's actual purchase. Confirmed receipt prices remain primary and are
available through the product price-history endpoint and the read-only price
insights endpoint with store and known variant context. Only lines actually
committed to Vorrio stock participate. The PWA calls these values historic
household observations because they do not prove a current shelf price,
promotion or availability.

## GS1

GS1 services can validate whether a GTIN is assigned to an expected company.
They are not an open universal product catalog and have access limits, so GS1 is
an optional validation adapter rather than the default lookup.

## Expiry dates

A normal EAN-13 barcode does not encode an expiry date. Vorrio accepts an exact
best-before date only from the receipt, a label scan or a supported GS1 Digital
Link/2D application identifier such as `15` or `17`. Otherwise the product's
default shelf-life remains an editable planning value, not a fact about a lot.

## Analysis-provider recommendations

The selected model may normalize retailer wording and propose local master
data. Exact price, quantity, barcode, branch and date values must come from the
receipt or package. New local data is created only after visible confirmation.
