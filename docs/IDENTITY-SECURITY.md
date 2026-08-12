# Identity and authentication architecture

## Current boundary

Version 0.8.16 has one explicit household, separate local user identities,
one-time invitations, constrained memberships, individually revocable browser
sessions, passkeys, optional TOTP, single-use recovery codes and scoped
automation tokens. The same-origin
`HttpOnly` cookie contains a random token protected by the application
signature. Only its SHA-256 hash is stored in SQLite. A revoked, expired or
unknown token fails server authentication immediately; changing UI state alone
cannot restore it.

Password-only login remains compatible while exactly one active user exists
and that user has not enabled TOTP.
After the first invited account is accepted, the login requires a unique local
email plus that user's password. TOTP adds a second factor to password login;
passkeys provide passwordless login. No recovery email is sent. Recovery codes
are created locally, shown once and can create a normal revocable session so
the user can replace a forgotten password. Direct public HTTPS additionally
requires every enforced external-path gate and explicit operator
acknowledgement; private VPN/HTTPS remains preferred.

The current baseline also applies exact trusted-host checks, restricted proxy
headers, same-origin validation for state changes, persistent per-source login
throttling, constant login failure text and append-only audit events for
authentication and authenticated mutations. Source addresses are HMAC
fingerprinted before storage; raw client IPs are not written to the audit
tables.

For safe offline package capture, a previously authenticated browser stores one
non-secret local hint that permits rendering only the precached PWA shell and
offline queue while the server is unavailable. The hint cannot authorize an
API request. The queue contains barcode, intended action, timestamp and a
client mutation ID, but no password, cookie, receipt, catalog result or stock
data. Server authentication and the normal explicit review are required after
reconnection.

## Shipped identity foundation

The additive schema now includes:

- `households` as the future tenant and encryption boundary;
- `users` for local identities, independent password hashes and lifecycle state;
- `household_memberships` with an owner/admin/member/viewer role constraint;
- `auth_sessions` with a hashed random token, privacy-safe device label,
  creation/last-seen/expiry times, most recent authentication method/time and a
  revocation timestamp;
- `household_invitations` with hashed random one-time tokens, recipient email,
  proposed role, expiry and acceptance/revocation state;
- `webauthn_credentials` and five-minute one-use `webauthn_challenges` for
  public keys, signature counters, exact origins and relying-party hosts;
- `totp_credentials` for encrypted secrets and the last accepted time step;
- `recovery_codes` and `login_challenges`, storing only hashes of raw
  single-use values;
- `api_tokens` with a hash-only random bearer secret, creator/household links,
  explicit scopes, expiry, last-use and revocation timestamps.

The PWA lists active sessions under **Einstellungen → Konto & Sicherheit**.
Revoking the current row logs out that browser; revoking another row takes
effect on its next API call. **Andere Geräte abmelden** preserves only the
current token. The full user agent and raw client IP are not persisted. Owner
and Admin can list the household; only Owner can grant Admin or modify Admin
accounts. Blocking a member revokes every session for that account.

## Remaining identity model

The next identity stages add:

- `device_authorizations` for native-client revocation;
- an Owner-facing read-only view of the already persisted `audit_events`.

Every household-owned domain table needs an immutable `household_id` before
multi-household mode is enabled. Filtering only in the user interface is not a
security boundary.

## Roles

| Role | Intended permissions |
|---|---|
| Owner | Security settings, members, backups, connectors and all household data. |
| Admin | Non-admin members, catalog and normal household workflows; no connectors or Owner security. |
| Member | Receipt review/import, scanner, stock count and shopping-list workflows. |
| Viewer | Read-only catalog, prices, receipts, stock and shopping access. |

Permissions are enforced in the REST API and tested there. Hiding a button is
only a usability measure.

## Authentication methods

Passkeys through WebAuthn are the preferred primary method because they are
phishing-resistant and can provide passwordless multi-factor authentication.
They require HTTPS and a stable relying-party domain. Vorrio verifies the
browser origin against `ALLOWED_ORIGINS`/`PUBLIC_URL`, requires user verification
and stores only the public credential material and signature counter.

Password login remains available for simple private installs. TOTP is an
optional second factor for password users and rejects reuse of an accepted time
step. SMS is not a security factor. Each account can register more than one
passkey. Ten high-entropy recovery codes can be generated or replaced; only
their SHA-256 hashes are retained and each code works once.

Security-sensitive mutations accept only a session authenticated within the
last ten minutes. Reconfirmation uses the current password and, when TOTP is
enabled, a valid authenticator or recovery code. Recovery-code login is itself
recent authentication so a lost password can be changed immediately; all other
browser sessions are revoked by that password change.

### Automation tokens

Owner and Admin can create an expiring token for a non-human client after a
recent identity confirmation. The raw value is returned exactly once and has
the form `vor_pat_<prefix>_<secret>`; SQLite stores only its SHA-256 hash. The
visible prefix identifies a deployed token without revealing it. Tokens expire
after 1–365 days, can be revoked immediately and are disabled when their
creator or membership is blocked.

Send the value only as `Authorization: Bearer <token>` over HTTPS. A bearer
request never falls back to a valid browser cookie when the supplied token is
invalid, and an API token cannot call identity, settings, connector, receipt
upload or direct catalog-mutation endpoints. The creator's current household
role remains an additional authorization boundary.

| Scope | Allows |
|---|---|
| `status:read` | Instance and connector status. |
| `catalog:read` | Products, barcodes and master data. |
| `stock:read` | Stock-count product totals and count history. |
| `shopping:read` | Shopping list and low-stock preview. |
| `shopping:write` | Reviewed list generation and list-item updates. |
| `scans:read` | Scan drafts and unresolved-code inbox. |
| `scans:write` | Resolve, edit, confirm or discard scan drafts. |

The PWA provides a read-only Home Assistant preset and a scanner preset. Custom
scope selection is available for other local services. OpenAPI marks each
bearer-enabled operation with `x-vorrio-required-scope`.

Optional OIDC can later connect Authentik or another standards-compliant
identity provider. Local accounts remain supported so a self-hosted household
cannot lock itself out merely because an external identity service is down.

## Migration from the household password

On an existing installation Vorrio reuses the current password hash and creates
exactly one household/Owner membership. A valid 0.8.8 signed cookie is upgraded
in place on its first request: the browser receives a random session token and
the database stores only its hash. Catalog, stock, receipts, files and connector
settings are not rewritten.

The Owner can keep working before naming the migrated profile. A highlighted
settings card requests a display name and optional local email; saving it marks
the bootstrap complete. This avoids an unattended upgrade locking out the
household. New installations collect the Owner name during first-run setup.

The 0.8.11 migration adds authenticator and challenge tables plus two additive
session fields. Existing sessions are backfilled from their creation time,
which means an older still-valid browser remains logged in but must confirm the
password before a sensitive change. No catalog, receipt, stock or connector
record is rewritten.

The 0.8.12 migration adds only the `api_tokens` table and indexes. It creates no
token automatically and does not rewrite users, sessions or household domain
data.

The 0.8.13 migration adds personal notification preferences, encrypted push
devices, condition-transition events and bounded delivery records. Push stays
disabled until a user opts in from an HTTPS PWA. The same guarded secret
rotation re-encrypts VAPID, TOTP, connector and push-subscription secrets.

Member invitations use 72-hour single-use links. Their raw random token is
shown only in the creation response, while the database stores only a SHA-256
hash. The recipient chooses an independent password during acceptance. SMTP
may be an optional delivery mechanism later but is not required.

## Internet-exposure security controls

- persistent privacy-safe source login throttling plus an edge-rate-limit
  requirement for direct internet deployments;
- constant authentication error messages and security-event logging (baseline
  shipped);
- CSRF/origin checks for cookie-authenticated state changes (shipped);
- Secure, HttpOnly and appropriate SameSite cookies over HTTPS;
- trusted-host and trusted-proxy enforcement (shipped);
- session list, privacy-safe device names, all-other logout and individual
  revocation (shipped in 0.8.9);
- additional users, one-time invitations and API-enforced role permissions
  (shipped in 0.8.10);
- passkeys, optional TOTP, one-time recovery codes and tested recovery login
  (shipped in 0.8.11);
- recent-authentication checks for security, family and connector changes
  (shipped in 0.8.11; offline backup administration remains operational);
- scoped, expiring API tokens instead of sharing a human session (shipped in
  0.8.12);
- audit records for login, MFA, membership, permission and token changes;
- upload type validation, decompression limits and isolated PDF/image parsing;
- dependency, container and release security checks.

The complete enforced profile, test evidence and residual operator duties live
in [External-access security review](EXTERNAL-ACCESS-SECURITY-REVIEW.md).

Passwords should migrate to a current memory-hard password-hashing policy
without invalidating existing scrypt hashes: verify the old hash once and
rehash it on successful login.
