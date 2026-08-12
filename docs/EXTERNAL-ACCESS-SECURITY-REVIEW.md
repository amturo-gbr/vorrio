# External-access security review

Review date: 2026-08-12
Release: 0.8.17
Scope: Browser/PWA -> TLS reverse proxy or tunnel -> Uvicorn -> Vorrio REST API

## Outcome

The application path is approved for deliberate `public_https` deployments
only when every enforced readiness condition passes and the operator explicitly
sets `PUBLIC_EXPOSURE_ACKNOWLEDGED=true`. An incomplete public profile now
returns HTTP 503 for the PWA and API; only liveness and the secret-free readiness
diagnostic remain reachable. Selecting a weaker profile to bypass this gate is
not a supported public deployment.

Private VPN/HTTPS remains the preferred household setup because it exposes less
attack surface. Passing this review does not automatically publish a route,
change DNS or open a router port.

## Reviewed trust boundaries

- TLS terminates at a maintained proxy or tunnel; only its actual address or
  network may supply forwarded headers.
- The original dedicated hostname is preserved and must match both
  `TRUSTED_HOSTS` and the canonical `PUBLIC_URL`.
- Cookie-authenticated state changes require an exact approved Origin in HTTPS
  profiles. Bearer API clients remain usable without a browser Origin, but only
  on explicitly scoped endpoints.
- Session cookies are signed, `HttpOnly`, `SameSite=Lax` and `Secure`.
- API responses are `Cache-Control: no-store`; browser responses receive HSTS,
  a restrictive CSP, frame denial, no-sniff, no-referrer and opener isolation.
- Public Web Push subscriptions must be HTTPS and resolve only to globally
  routable addresses. Local, private, link-local and reserved targets are
  rejected.
- Grocy and local AI connectors deliberately may reach private networks because
  that is their self-hosted purpose. Only an Owner with recent authentication
  can change their validated HTTP(S) base URLs; embedded credentials, fragments,
  query strings and special-purpose literal targets are refused and redirects
  remain disabled.
- Receipt uploads retain byte, pixel, format and PDF-render limits before any AI
  provider sees content. Provider output and product databases remain untrusted,
  review-before-write inputs.

## Enforced public profile

```env
DEPLOYMENT_PROFILE=public_https
PUBLIC_URL=https://vorrio.example.com
TRUSTED_HOSTS=vorrio.example.com
ALLOWED_ORIGINS=https://vorrio.example.com
FORWARDED_ALLOW_IPS=172.20.0.0/16
SESSION_HTTPS_ONLY=true
PUBLIC_EXPOSURE_ACKNOWLEDGED=true
PUBLISHED_ADDRESS=127.0.0.1
```

`APP_SECRET_KEY` must also be unique and at least 32 characters. The published
address example assumes the reverse proxy runs on the Docker host. If it runs
in Docker, connect both services through a private Docker network and omit the
host-published application port instead.

Before setting the acknowledgement, verify that there is no second path around
the proxy: no WAN port-forward to `9380`, no public host firewall rule, and no
directly published Docker socket, data volume or SQLite file.

## Repeatable evidence

`make check` includes `external-path-test`. The isolated production-image smoke
asserts a ready public profile, CSP/HSTS, Secure/HttpOnly/SameSite cookies,
trusted-host rejection, cross-origin rejection, missing-Origin rejection for an
authenticated cookie, no-store API responses and disabled TRACE. Unit tests also
prove that incomplete public profiles are fail-closed and unsafe outbound URLs
are rejected.

The review additionally exercised a real Uvicorn container through simulated
trusted reverse-proxy headers. It returned `ready` with HSTS for the canonical
host and HTTP 400 for an untrusted host.

## Residual operator responsibilities

- Keep the proxy, container runtime and host patched; run the image vulnerability
  gate on every release.
- Add an edge request-rate limit for internet deployments. Vorrio's persistent
  privacy-safe source throttling is the application backstop, not a replacement
  for volumetric protection.
- Prefer passkeys and enable TOTP/recovery codes before remote use. Store recovery
  codes outside Vorrio and periodically review sessions, tokens and audit events.
- Back up `/data` and `APP_SECRET_KEY` separately and test restoration.
- A future public project release still needs the final security contact,
  coordinated-disclosure address and an independent review policy.
