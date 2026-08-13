# Configuration

## Environment variables

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `VORRIO_VERSION` | release Compose only | `0.8.24` | Versioned GHCR tag selected by `docker-compose.release.yml`. |
| `APP_SECRET_KEY` | yes | development fallback | Encrypts provider/connector, TOTP, VAPID and push-subscription secrets and signs the cookie carrying a random server-session token. |
| `APP_PASSWORD` | no | empty | Optional preconfigured household password; empty enables first-run setup. |
| `DEPLOYMENT_PROFILE` | no | `lan` | Selects `lan`, `private_https` or the guarded `public_https` policy. |
| `PUBLIC_URL` | HTTPS profiles | empty | Canonical origin for generated links and origin validation; no path prefix. |
| `TRUSTED_HOSTS` | external access | `*` | Comma-separated HTTP hostnames. The wildcard is LAN-only. |
| `ALLOWED_ORIGINS` | passkeys/HTTPS | empty | Exact browser origins accepted by the CSRF guard and passkey ceremonies; does not enable wildcard CORS. |
| `FORWARDED_ALLOW_IPS` | behind proxy | `127.0.0.1` | Comma-separated proxy IPs/networks allowed to supply `X-Forwarded-*`. Never use `*` on an exposed service. |
| `SESSION_HTTPS_ONLY` | HTTPS profiles | `false` | Adds the Secure flag to session cookies. |
| `PUBLIC_EXPOSURE_ACKNOWLEDGED` | public HTTPS | `false` | Explicit final acknowledgement; public application traffic remains HTTP 503 until every other security condition also passes. |
| `PUBLISHED_ADDRESS` | no | `0.0.0.0` | Host address used for Compose port `9380`; use `127.0.0.1` with a host proxy or a private Docker network without a published app port. |
| `VORRIO_DATA_VOLUME` | release Compose/Portainer | `vorrio_data` | Named Docker volume used for persistent application data. |
| `MAX_UPLOAD_MB` | no | `12` | Maximum receipt image or PDF size. |
| `MAX_REQUEST_MB` | no | `13` | Maximum complete HTTP request including multipart overhead. |
| `MAX_IMAGE_MEGAPIXELS` | no | `40` | Pixel limit checked before image analysis. |
| `RECEIPT_RETENTION_DAYS` | no | `7` | Default retained receipt-file period. |
| `LOGIN_MAX_FAILURES` | no | `5` | Failed logins allowed per privacy-safe source fingerprint in the time window. |
| `LOGIN_WINDOW_SECONDS` | no | `900` | Login throttling window and retry interval. |
| `WEB_PUSH_SUBJECT` | no | `mailto:admin@vorrio.local` | VAPID contact claim; use a real `mailto:` or HTTPS contact for a distributed production image. |
| `NOTIFICATION_CHECK_SECONDS` | no | `900` | Low-stock/expiry evaluation interval, constrained to 60–86400 seconds. |
| `DATA_DIR` | container-managed | `/data` | Database and retained receipt location. |
| `TZ` | no | deployment-specific | Container timezone used for operational logs. |

Do not pass provider or Grocy keys through committed Compose files. Enter them
through the authenticated settings screen; they are encrypted before storage.

These deployment variables are enforced in 0.8.16. Check `/api/readiness` after
every hostname, TLS or reverse-proxy change. The endpoint exposes only safe
pass/warn/fail diagnostics, not configured secrets or network lists. See
[Deployment profiles and URLs](DEPLOYMENT-PROFILES.md).
The acknowledgement and complete checklist are documented in
[External-access security review](EXTERNAL-ACCESS-SECURITY-REVIEW.md).

The authenticated privacy setting controls both new uploads and the scheduled
source-file evaluator. The process waits five minutes after startup, then runs
hourly. Owners can preview and apply the same rule immediately; there is no
separate cron or environment variable to keep in sync.

## Analysis providers

Choose the provider, base URL, vision-capable model and API key in Settings.
Ollama can run without a key. See [AI providers](AI-PROVIDERS.md).

Receipt media leaves the server only when a remote provider is selected. PDF
rendering and embedded-text extraction happen locally first.

## Interface language

There is no deployment-wide language environment variable. German or English
is selected per account and stored in the local database. Both official
data-only packs ship in the same image; the PWA loads and caches the selected
catalog on demand. Before sign-in the browser and last local choice provide the
initial language; after sign-in the account preference wins. See
[Localization](LOCALIZATION.md).

## Web Push

Push is disabled until each user explicitly enables an HTTPS PWA device. No
SMTP or hosted notification account is needed. See
[Web Push notifications](NOTIFICATIONS.md) for the device flow, event rules and
encrypted key lifecycle.

## Household budget

The shared monthly EUR target is application data rather than an environment
variable. Owner or Admin configures it under **Einkäufe → Budget**. Leaving it
unset still shows confirmed spending history. See [Household budget](BUDGET.md)
for counting, permissions and forecast boundaries.

## Grocy connector

Grocy is disabled on new installations. Enabling it requires a URL and normal
user API key. The connector supports catalog migration and one-way export; it
does not become Vorrio's source of truth.

Disabling the connector keeps its encrypted key and mappings so it can be
re-enabled without data loss.

## Receipt privacy

Enable “delete after analysis” to remove the uploaded source immediately after
structured extraction. Parsed receipt data, review decisions and stock
movements remain in SQLite.
