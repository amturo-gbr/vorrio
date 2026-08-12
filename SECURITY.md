# Security policy

Report vulnerabilities privately to the Amturo UG maintainers before opening a
public issue. The public repository uses
[GitHub private vulnerability reporting](https://github.com/amturo-gbr/vorrio/security/advisories/new);
the maintainer must enable that repository setting before launch.

Do not include secrets, session cookies, receipt images, household addresses or
database exports in a report. Use synthetic reproduction data.

## Supported versions

Only the latest 0.x release receives security fixes before the stable 1.0
support policy is published.

## Security boundaries

- Provider and connector secrets are encrypted at rest with `APP_SECRET_KEY`.
- The public settings API returns only `*_configured` flags, never keys.
- Browser cookies are signed, `HttpOnly` and `SameSite=Lax`. They carry a
  random token whose hash maps to an expiring, individually revocable
  server-side session; production HTTPS installations should set
  `SESSION_HTTPS_ONLY=true`.
- Every stock-changing receipt intake requires an authenticated session and
  explicit user confirmation.
- WebAuthn passkeys are verified against a one-time server challenge, the exact
  allowed HTTPS origin and its relying-party hostname; private keys never reach
  Vorrio.
- Optional TOTP secrets are encrypted with `APP_SECRET_KEY`, accepted time
  steps cannot be replayed, and recovery codes are stored only as hashes and
  consumed once.
- Authenticator, password, family-permission and connector changes require an
  authentication no older than ten minutes.
- Automation API tokens carry a 256-bit random secret, are stored only as a
  SHA-256 hash, expire after at most one year and authorize only their explicit
  scopes. Identity, settings, connector and unreviewed catalog/receipt writes
  remain unavailable to bearer tokens.
- Web Push is explicit opt-in in a secure browser context. Subscription
  endpoints/keys and the VAPID private key are encrypted at rest; bearer tokens
  cannot manage personal devices. Dead 404/410 subscriptions are revoked and
  delivery records exclude notification text, raw IPs and full user agents.
- Fuzzy names stay review-only.
- Duplicate-file hashes, conservative semantic receipt fingerprints, receipt
  locks and database uniqueness constraints protect against accidental repeat
  imports.
- Receipt files can be deleted immediately after analysis or by the previewed
  hourly/manual retention rule; paths outside the receipt directory are refused.
- Household product-photo uploads accept validated JPEG, PNG or WebP only,
  discard camera metadata, are size-bounded and require authentication to read.
- External product data is untrusted input and is shown with provenance before
  confirmed local values are changed.
- Remote AI-provider failure bodies are not forwarded to browsers or audit
  views; users receive only a bounded HTTP-status category and remediation hint.
- Trusted hosts, restricted forwarded headers and exact origin checks protect
  the browser deployment boundary.
- Failed logins are throttled per HMAC-fingerprinted source; authentication and
  authenticated mutations create append-only audit events without raw IPs.
- Request, file, image-pixel and PDF render limits are enforced before provider
  analysis.
- Offline scanning stores only barcode, intended mode, timestamp and a stable
  idempotency key in that browser. A local prior-login hint can reopen the
  cached shell but is never server authentication; passwords, cookies, catalog
  and receipt data are not copied into application storage.
- Budget settings require an Owner or Admin browser session. The change audit
  records configuration state and threshold but not the monetary limit; budget
  reads use reviewed receipts only and contain no bank-account data.
- Portable export, retention execution and complete erasure are Owner-only and
  recent-authenticated. Exports omit credentials and fingerprints; erasure
  requires an exact phrase plus a second PWA confirmation.
- Default client-address access logs are disabled. Structured request logs use
  only random request ID, route template, method, status and duration. The
  Owner operations API omits audit detail JSON and source fingerprints.

## Vulnerability scanning and VEX

CI blocks fixed High/Critical findings in the production image. A maintained
[OpenVEX assessment](security/vex.openvex.json) may suppress a scanner match
only when the affected code path is demonstrably unreachable in Vorrio. Each
statement names the CVE, product, standardized justification, technical impact
reason and assessment timestamp. Package updates remain mandatory when a stable
compatible fix exists; VEX is not a substitute for upgrades.

For 0.8.18, the High finding `CVE-2026-15308` affects CPython's incremental
`html.parser.HTMLParser`. Vorrio neither imports that parser nor accepts HTML as
a receipt format; bounded untrusted inputs are validated as image or PDF data.
The VEX statement therefore records `vulnerable_code_not_in_execute_path` while
the project remains on stable Python 3.14. Reassess and remove the statement
when a patched stable CPython base image is available or if HTML parsing is
introduced.

The scanner can additionally report lower-severity runtime findings that do
not fail the High/Critical release threshold. They remain visible in CI and
must be reassessed on every base-image update; they are not hidden by this VEX
statement.

## Internet exposure

Version 0.8.18 includes the dedicated external-path application review. HTTPS
alone still does not make an installation safe: `public_https` refuses normal
application traffic until canonical host/origin, trusted proxy, Secure-cookie,
secret and explicit acknowledgement checks all pass. Private VPN/HTTPS remains
the preferred household profile. See the documented residual operator duties
in [External-access security review](docs/EXTERNAL-ACCESS-SECURITY-REVIEW.md).

Treat an API token like a password. Transmit it only in the
`Authorization: Bearer` header over a trusted HTTPS/VPN path, store it in the
target system's secret store, choose the smallest preset or scope set, and
revoke it when a device is retired. Never place bearer values in URLs or logs.

Use HTTPS, keep authentication enabled, restrict administrative networks and
back up the data volume. Never expose the SQLite file, `APP_SECRET_KEY`,
provider keys or connector keys through a web server. See
[Identity and authentication](docs/IDENTITY-SECURITY.md),
[Deployment profiles](docs/DEPLOYMENT-PROFILES.md) and the
[foundation checklist](docs/FOUNDATION-CHECKLIST.md).
