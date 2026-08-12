# Web Push notifications

Vorrio 0.8.14 can send personal, opt-in browser notifications when a product
enters its low-stock state or a stock lot enters the configured best-before
window. No notification permission is requested automatically and no external
notification account is required.

## User workflow

1. Open Vorrio through its stable private HTTPS URL.
2. On iPhone or iPad, add Vorrio to the Home Screen and open that installed app.
3. Sign in and open **Settings → Stock notifications**.
4. Choose **Allow notifications** and accept the operating-system prompt.
5. Select low-stock and/or expiry alerts, choose the expiry window and save.
6. Use **Send test** to verify the current device.

Each browser installation is a separate device subscription. Removing a device
revokes its server record and unsubscribes the current browser. The global
personal switch can pause delivery while keeping the devices registered.

## Event behavior

- Low stock is eligible only when `minimum_stock_quantity > 0` and the summed
  current lots are at or below that minimum.
- Expiry is eligible only for a lot with remaining quantity and a best-before
  date inside the user's 0–90 day warning window.
- Vorrio sends one event when the condition becomes active. Repeated checks do
  not repeat it.
- The event becomes eligible again only after the stock recovers or the expiry
  condition disappears. Disabling a notification kind also resolves its open
  events, so deliberately re-enabling it evaluates the current state afresh.
- A failed delivery remains retryable. HTTP 404/410 responses from a push
  service revoke the dead device automatically.

The in-process evaluator runs every 15 minutes by default. It is intentionally
small and appropriate for the supported single-container/single-household
deployment. A persistent external job queue remains a later scale-out gate.

## Privacy and key storage

Browser subscription endpoints and their `p256dh`/`auth` keys are encrypted at
rest with `APP_SECRET_KEY`. The VAPID private key is generated locally on first
use and encrypted with the same key; only its public application-server key is
returned to an authenticated browser. Vorrio keeps bounded 90-day delivery
records without message content, raw IP addresses or full user-agent strings.

Rotating `APP_SECRET_KEY` re-encrypts connection settings, TOTP secrets, the
VAPID key and every push subscription before invalidating browser sessions.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `WEB_PUSH_SUBJECT` | `mailto:admin@vorrio.local` | VAPID contact claim. Public distributions should use a real `mailto:` or HTTPS contact. |
| `NOTIFICATION_CHECK_SECONDS` | `900` | Evaluation interval, constrained to 60–86400 seconds. |

Web Push requires a secure browser context. LAN HTTP remains available for
manual use but cannot register camera, passkey or push capabilities. iOS and
iPadOS support standards-based Web Push for Home Screen web apps starting with
16.4; the permission prompt must follow a direct user action.

## REST API

Authenticated cookie sessions use:

- `GET /api/v1/notifications/state`
- `PUT /api/v1/notifications/preferences`
- `POST /api/v1/notifications/subscriptions`
- `DELETE /api/v1/notifications/subscriptions/{subscription_id}`
- `POST /api/v1/notifications/test`

Automation bearer tokens cannot manage personal push devices. Request and
response schemas are part of the checked-in OpenAPI contract.
