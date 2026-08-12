# Data privacy, portability and erasure

Vorrio is local-first, but local data still needs an understandable lifecycle.
Version 0.8.15 gives the household Owner one place under **Einstellungen** to
inspect storage, download a portable copy, apply the receipt-file retention
rule and erase the single-household installation.

## Portable export

`GET /api/v1/privacy/export/preview` reports the records and retained source
files that can be exported. `GET /api/v1/privacy/export` returns a ZIP after a
recent Owner authentication. The caller may exclude receipt images/PDFs while
keeping all recognized receipt data.

The ZIP contains a versioned `manifest.json`, SHA-256 checksums and readable
JSON sections for household/member metadata, public preferences, catalog,
receipts, stock, shopping, scans and a sanitized audit history. It deliberately
excludes password hashes, raw or hashed session/invitation/API tokens, TOTP and
recovery material, passkey keys/challenges, provider/connector keys, Web Push
endpoints/keys and network-source fingerprints.

This is a portable household-data export, not a disaster-recovery backup. A
working restore still requires the complete `/data` volume and the matching
`APP_SECRET_KEY`; see [Backup and restore](BACKUP-RESTORE.md).

## Receipt-file retention

The privacy setting applies to source images and PDFs only. Recognized lines,
confirmed mappings, prices, receipts and stock movements remain available.

- **Nach Analyse löschen** removes the source immediately after successful
  analysis and makes older retained files eligible at the next cleanup.
- **Aufbewahrung in Tagen** keeps sources until the configured cutoff. `0`
  means eligible immediately.
- Vorrio evaluates the rule in the single application container after startup
  and then hourly. The Owner can preview and run it immediately.
- A database path that resolves outside `/data/receipts` is rejected and never
  deleted. The rejected pointer stays visible for operator repair.

## Operational view and audit minimization

The Owner view reports SQLite `quick_check`, database size, active session and
device counts, pending work, failures in the last 24 hours and recent events.
It does not return raw IP addresses, source fingerprints, audit-detail JSON,
request query strings or resource identifiers embedded in URLs. HTTP logs use
the API route template, status, duration and a random request ID only; default
Uvicorn client-address access logging is disabled.

## Permanent erasure

`DELETE /api/v1/privacy/household` is Owner-only, requires authentication from
the last ten minutes and accepts only the literal confirmation
`HAUSHALT ENDGÜLTIG LÖSCHEN`. The PWA adds a second browser confirmation. It
deletes accounts, sessions, settings, catalog, receipts, stock, shopping data,
audit records and retained receipt files, then returns the installation to
first-run setup.

Erasure is intentionally installation-wide because Vorrio currently supports
one household per deployment. It cannot be undone. Download an export and make
a tested volume backup first. Automated tests run erasure only against a fresh
temporary database; release checks never invoke it against a deployed volume.

## REST endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/privacy/export/preview` | Preview portable data and file size |
| `GET` | `/api/v1/privacy/export` | Download secret-free ZIP |
| `GET` | `/api/v1/privacy/retention` | Preview eligible source files |
| `POST` | `/api/v1/privacy/retention/run` | Apply the configured rule now |
| `GET` | `/api/v1/operations/overview` | Read privacy-safe health and audit summary |
| `DELETE` | `/api/v1/privacy/household` | Permanently erase the installation |

All endpoints require the Owner's browser session. Export, manual cleanup and
erasure additionally require recent authentication and are unavailable to API
tokens.
