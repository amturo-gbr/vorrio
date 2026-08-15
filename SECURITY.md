# Security policy

Report vulnerabilities privately to the Amturo UG maintainers before opening a
public issue. During the private release rehearsal, use `info@amturo.de`. Before
the repository becomes public, the maintainers enable
[GitHub private vulnerability reporting](https://github.com/amturo-gbr/vorrio/security/advisories/new)
and make it the preferred reporting channel.

Do not include secrets, session cookies, receipt images, household addresses or
database exports in a report. Use synthetic reproduction data.

## Supported versions

Only the latest 0.x release receives security fixes before the stable 1.0
support policy is published.

## Repository and release integrity

The 0.8.22 pre-publication review covered every reachable Git commit, all
tracked and unignored release files, the built runtime image, the attached
CycloneDX SBOM and immutable-digest asset. It found no credential, private
installation path or household data. The two scanner matches were the literal
`YOUR_TOKEN` examples in the automation guide; only that exact documentation
placeholder is allowlisted.

`make check` now scans the complete Git history with a digest-pinned Gitleaks
CLI image. The release-package contract independently blocks environment files,
databases, key material, common provider tokens, credential-bearing URLs and
personal macOS paths. It also enforces Amturo UG as the canonical
developer/maintainer in the author file, notice, README,
frontend repository metadata and OpenAPI contact. GitHub Actions checkouts use
full history so a secret in an earlier commit cannot be hidden by a shallow
clone.

The 0.8.26 pre-publication audit on 15 August 2026 repeated the full-history
and exact working-tree scans and reviewed all 256 publishable files. It found no
household LAN address, private installation hostname, personal workstation
path, database, receipt, cookie or provider credential. The explicitly checked
Cloudflare, R2 and Uptime credential forms were absent from every reachable
commit. All 86 tracked image assets use synthetic content; their metadata
contains no GPS position, camera/device identity, author or capture timestamp.

The release-package gate also rejects forced additions that Git would normally
ignore: `.env.*` files, cookie/session/HAR files, local data and browser-test
directories, build output, private IPv4 addresses and Cloudflare account/R2
endpoints. It also rejects source/history attribution to interactive development
assistants while allowing ordinary documentation of Vorrio's configurable AI
providers. These checks are regression-tested and are independent of Gitleaks.

The website source intentionally contains Amturo UG's legal company identity,
managing directors, registered office, register details, public phone number
and `info@amturo.de` in the German and English imprint/privacy pages. Those are
deliberate public legal disclosures, not household application data. They must
be reviewed by Amturo immediately before repository and website publication.

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

The 0.8.26 image scan reports one Medium CPython finding,
[`CVE-2025-15367`](https://github.com/python/cpython/issues/143923), in the
standard-library `poplib` command API. Vorrio does not import or call `poplib`
and exposes no POP3 feature. The only scanner-listed fix is currently a Python
3.15 alpha build, so the finding remains visible rather than moving the stable
runtime to a pre-release interpreter. Reassess when a stable patched base is
available or if POP3 support is ever introduced. Bandit found no Medium or High
issue in the runtime application; its Low findings are confined to fixed-argument
release tooling, test assertions and explicitly synthetic smoke-test passwords.
The production npm audit reports zero findings. `npm ci` does emit an upstream
deprecation notice because the current `vite-plugin-pwa`/`workbox-build` chain
still pins `glob` 11.1.0; it is a build-stage-only dependency, has no npm audit
advisory in this lockfile and is absent from the final Python runtime image.
Track the upstream update without overriding Workbox's tested dependency range.

## Internet exposure

Version 0.8.22 includes the dedicated external-path application review. HTTPS
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
