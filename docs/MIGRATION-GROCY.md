# Migrating from Grocy

Vorrio can coexist with Grocy while a household changes workflows.

## Safe sequence

1. Back up both applications.
2. Configure the Grocy URL and normal-user API key in Vorrio.
3. Leave the connector enabled during the transition.
4. Select “Katalog übernehmen” in Vorrio Settings.
5. Review product, location, unit and group counts.
6. Open **Vorrat → Zählen**, load the optional **Grocy-Vorschlag** and review
   every mapped previous/proposed balance. Count or correct physical stock
   before confirming.
7. Resolve unmapped Grocy products through catalog import or deliberate local
   product creation; they are never created by the stock preview.
8. Use Vorrio for new receipt intake.
9. Disable the connector after Grocy export and preview are no longer needed.

Catalog import is additive and idempotent. Grocy identifiers are stored as
external references; repeated imports update metadata without duplicating a
product.

## Stock quantities

Catalog import still imports metadata, not quantities. Version 0.8.2 adds a
separate read-only stock preview because historic receipts cannot reconstruct
consumption, manual corrections or expired stock reliably.

The preview aggregates Grocy lot rows, maps only products carrying an imported
Grocy identifier and lists positive unmatched entries separately. It writes
nothing. After a person reviews and confirms the draft, Vorrio records a local
count session and movements. Grocy remains unchanged and is not treated as a
bidirectional synchronization source.

## Rollback

Disabling the connector changes no Grocy data. If a Vorrio release must be
rolled back, restore the pre-upgrade Vorrio volume with the matching image and
secret key. Do not run an older binary against a migrated only-copy database.
