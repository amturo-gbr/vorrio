# Installation

## Requirements

- Docker Engine 24 or newer;
- Docker Compose v2;
- 1 CPU core and 512 MB RAM for the application;
- persistent local storage for `/data`;
- an analysis provider, unless a local Ollama-compatible model is used.

SQLite should stay on a local Docker volume. Avoid network filesystems that do
not provide reliable file locking.

## Docker Compose

```bash
git clone https://github.com/amturo/vorrio.git
cd vorrio
cp .env.example .env
openssl rand -hex 32
```

Place the generated value in `.env` as `APP_SECRET_KEY`, then start:

```bash
docker compose up -d --build
docker compose ps
```

Open `http://SERVER:9380`, name the first Owner and complete the password setup.

For a LAN installation, replace the wildcard with the exact names or IPs used
by browsers whenever practical:

```env
DEPLOYMENT_PROFILE=lan
TRUSTED_HOSTS=localhost,vorrio.lan,192.0.2.10
FORWARDED_ALLOW_IPS=127.0.0.1
SESSION_HTTPS_ONLY=false
```

The documentation address is reserved and must be replaced with the real local
address. Check both liveness and deployment readiness:

```bash
curl http://SERVER:9380/api/health
curl http://SERVER:9380/api/readiness
```

The GitHub URL becomes available with the first public release. Before that,
use the source archive supplied by Amturo UG.

### Published GHCR image

After the first public tag exists, a normal household installation can pull
the signed image without building it locally:

```bash
cp .env.example .env
openssl rand -hex 32
```

Place the generated value in `.env` as `APP_SECRET_KEY`, then start:

```bash
docker compose -f docker-compose.release.yml pull
docker compose -f docker-compose.release.yml up -d
```

`VORRIO_VERSION` selects the versioned tag. Pin an immutable digest for a
long-lived production installation and verify its signature as described in
[Release and upgrade policy](RELEASES.md).

## Portainer

Create a stack from `stack.yml`, set `APP_SECRET_KEY` in the stack environment,
and deploy. Keep `APP_PASSWORD` empty to use browser-based initial setup.
`VORRIO_IMAGE` may select a versioned tag or immutable digest;
`VORRIO_DATA_VOLUME` preserves a chosen named volume across stack updates.

## Reverse proxy and HTTPS

Camera access and PWA installation work most reliably over HTTPS. Forward one
hostname to container port `8080`, replace untrusted forwarded headers, and set:

```env
DEPLOYMENT_PROFILE=private_https
PUBLIC_URL=https://vorrio.example.com
TRUSTED_HOSTS=vorrio.example.com
FORWARDED_ALLOW_IPS=192.0.2.20
ALLOWED_ORIGINS=https://vorrio.example.com
SESSION_HTTPS_ONLY=true
```

Complete first-run setup on a trusted network before publishing a route.
Version 0.8.18 supports guarded public HTTPS, but private VPN/HTTPS remains the
preferred household profile. Public traffic stays HTTP 503 until the complete
contract passes and `PUBLIC_EXPOSURE_ACKNOWLEDGED=true` is set deliberately.
The exact profiles and audit are documented in
[Deployment profiles and URLs](DEPLOYMENT-PROFILES.md) and
[External-access security review](EXTERNAL-ACCESS-SECURITY-REVIEW.md).
After deployment, see [Automation API tokens](AUTOMATION-TOKENS.md) before
connecting Home Assistant or a scanner station and
[Web Push notifications](NOTIFICATIONS.md) before enabling stock alerts.

The frontend uses same-origin relative API URLs. A different public hostname
does not require rebuilding Vorrio. Do not host it below a stripped path prefix
such as `/vorrio`; use a dedicated hostname.

### Private LAN HTTPS for camera testing

A maintained reverse proxy can issue an internal certificate for a private
hostname and forward it to Vorrio. Install the proxy's root CA only on the
household devices that should trust this installation. The hostname must be in
`TRUSTED_HOSTS`, the proxy network in `FORWARDED_ALLOW_IPS`, and the exact HTTPS
origin in `ALLOWED_ORIGINS`.

This is suitable for a private LAN or VPN. It is not a substitute for the
internet-exposure security gate. Prefer one stable hostname; changing local IPs
or temporary test names later creates a new browser origin and passkey identity.

### Mobile and installed PWA

Open the canonical HTTPS address in Safari or Chrome and use the platform's
**Add to Home Screen** action. Vorrio keeps the same origin and session in
standalone mode. Mobile controls use an iOS-safe focus size, preserve pinch zoom
and respect dynamic browser height plus top/bottom safe areas.

Run `make pwa-check` after changing viewport metadata, the manifest, global
layout or form styles. The check also validates service-worker registration and
that the install icon remains a square PNG of at least 512 pixels.

After one successful login, the installed PWA can reopen its cached shell while
the server is unavailable and queue package barcodes locally. This is not a
full offline copy: receipts, catalog, stock and authentication secrets are not
cached, and every queued scan still requires server-side resolution and normal
confirmation after reconnection.

## Update

1. Read `CHANGELOG.md` and migration notes.
2. Back up `/data`.
3. Pull or build the new pinned version.
4. Recreate the container without deleting the volume.
5. Check `/api/health`, `/api/readiness`, `/docs` and the PWA.

Schema migrations run idempotently at startup. Never downgrade against the only
copy of a migrated database; restore the matching backup instead.

The 0.8.9 migration adds one household boundary, one Owner identity and hashed
server-side browser sessions. An existing 0.8.8 signed login cookie is converted
on its first request without logging the browser out. The current password hash
is reused, while products, receipts, stock, images and connector settings are
left untouched. Complete the Owner name and optionally a local email under
**Einstellungen → Konto & Sicherheit** after the upgrade.

The 0.8.10 migration adds one-time household invitations without changing
existing users or sessions. Save a unique Owner email before creating the first
invitation. The link expires after 72 hours, can be accepted only once and lets
the recipient choose an independent password. As soon as two active users
exist, the login form requires email plus password. Blocking a member revokes
all of that account's sessions immediately.

The 0.8.11 migration adds passkey, TOTP, recovery-code and one-time challenge
tables plus the authentication time/method on browser sessions. Existing
sessions stay valid; sessions older than ten minutes must confirm the current
password before security, family or connector changes. Open Vorrio through one
stable allowed HTTPS hostname before creating a passkey. Existing catalog,
receipts, stock and connector values are unchanged.

The 0.8.12 migration adds the API-token table and indexes. It creates no
credential automatically. Existing accounts, browser sessions, catalog,
receipts, stock and connectors remain unchanged. Create a token only after the
upgrade under **Einstellungen → Konto & Sicherheit → API-Tokens**, copy its raw
value once and store it as a secret in the target service.

The 0.8.13 migration adds personal notification preferences, encrypted browser
subscriptions, state-transition events and bounded delivery records. Push stays
disabled and no browser permission is requested during the upgrade. Open the
stable private HTTPS PWA and opt in per device. The VAPID key is generated
locally on first notification-settings use and encrypted with `APP_SECRET_KEY`.

The 0.8.14 migration adds the optional `household_budget_settings` table and a
receipt-date index. It creates no target automatically and does not rewrite any
receipt, product, stock, shopping or connector row. Owner or Admin can configure
the shared EUR target later under **Einkäufe → Budget**.

Version 0.8.15 adds no destructive schema migration. It starts an hourly
receipt-source retention evaluator, adds Owner privacy/operations endpoints and
ships a responsive operations/export/retention/erasure interface. Existing
files use the already configured privacy rule. Review its preview after the
upgrade; scheduled cleanup does not run during the first five minutes.

Version 0.8.16 also adds no database migration and does not change household
data. Existing LAN/private-HTTPS deployments retain their profile and access.
Only a deliberately selected `public_https` profile gains the new runtime gate;
complete its readiness checklist before setting the acknowledgement.

The 0.7 migration adds `scan_drafts`, idempotency indexes and `opened_at` on
stock lots. It does not rewrite existing products, receipts, barcodes or stock.

The 0.7.1 migration adds nullable semantic receipt identities, match evidence
and receipt-to-variant links. Existing receipt rows are backfilled
conservatively; stock quantities and previous confirmations are not changed.
