# iOS and Android apps

## Decision

The PWA remains the fastest universal client. The planned store apps use
Capacitor 8 around the existing React application instead of starting an
independent React Native rewrite. The UI bundle is packaged inside each app;
the app does not download and display the Vorrio website as its interface.

Capacitor preserves the shared TypeScript and design system while allowing
native Swift and Android code where device integration needs it.

## Native value

The first store release must provide more than a website wrapper:

- native camera and barcode scanning;
- offline scan and receipt queue with visible synchronization state;
- push notifications with deep links for low stock, expiry and shared lists;
- share-sheet import for receipt images and PDFs;
- passkeys and platform credential managers;
- secure token storage, biometric re-entry and device-session management;
- background upload retry within platform limits;
- native app links and accessible platform navigation.

These capabilities also provide the utility expected by app-store review.

The scan experience shares the same modes and resolution rules as the PWA:
local catalog first, optional cached/external enrichment, explicit confirmation
and an unresolved-code inbox. See [Product scanning](BARCODE-SCANNING.md).

The 0.7 PWA already implements that shared REST contract and a responsive scan
surface. Its browser camera uses a bundled local decoder and HTTPS. Native
plugins later replace only device capture; resolution, review and confirmation
continue to use the same versioned API.

## Connecting a self-hosted server

On first launch the user enters an HTTPS server URL or scans a configuration QR
code. The QR code contains only public instance metadata, never a password,
API token or `APP_SECRET_KEY`.

A planned `/.well-known/vorrio` document exposes:

- instance name and stable instance identifier;
- API and minimum compatible client versions;
- canonical public URL;
- supported authentication methods;
- links for privacy, support and WebAuthn association metadata.

Release builds require a valid HTTPS certificate. They do not offer an
“ignore certificate errors” switch. Private certificate authorities must be
installed and trusted by the operating system. The browser PWA follows the same
rule for private camera-enabled HTTPS installations.

## Native authentication

The browser's same-origin session cookie is not reused as the native API
credential. Native apps use browser-based authorization with Authorization
Code plus PKCE, short-lived access tokens and rotating, revocable refresh
tokens. Tokens are scoped to one instance, household, user and device and are
stored in Keychain or Android Keystore-backed secure storage.

Wildcard credentialed CORS is prohibited. Each supported app origin and link
association is explicit. iOS Universal Links and Android App Links bind the
installed app to the same verified HTTPS domain used by passkeys.

Version 0.8.16 provides separate household accounts, role enforcement,
passkeys, optional TOTP, recovery codes and
revocable browser sessions plus scoped local automation tokens. Browser
sessions and automation tokens are intentionally not native refresh tokens; the
future PKCE authorization endpoint will create a separate
`device_authorization` tied to the same user and household.

The entered server must already satisfy Vorrio's external-path gate. A native
client does not set or bypass `PUBLIC_EXPOSURE_ACKNOWLEDGED`, relax trusted
hosts/origins, or fall back to an insecure LAN URL. See
[External-access security review](EXTERNAL-ACCESS-SECURITY-REVIEW.md).

## Delivery plan

1. Extend the shipped family-account/browser-session foundation with native
   device authorization and API compatibility discovery.
2. Add offline-safe mutation IDs and conflict responses to the REST API.
3. Create the shared Capacitor workspace and native scan/share plugins.
4. Test iOS through TestFlight and Android through an internal Play track.
5. Add privacy manifests, store privacy declarations, support and demo mode.
6. Publish iOS through Amturo UG and Android through Google Play; evaluate an
   F-Droid-compatible build after reproducible signing and update handling are
   established.
