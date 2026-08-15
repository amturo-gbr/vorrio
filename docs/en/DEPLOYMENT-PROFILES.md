# Deployment profiles and URLs

Vorrio's web client uses relative `/api/v1` URLs. The browser therefore talks
to the same origin that served the PWA. Version 0.8.16 does not require a hardcoded
external URL, and changing from a LAN hostname to an HTTPS hostname does not
require rebuilding the frontend.

Version 0.8.16 enforces trusted hosts, restricted forwarded headers, origin
checks, login throttling, resource limits, local family accounts, hashed
server-side browser sessions, REST role permissions, passkeys, optional TOTP,
single-use recovery codes, recent authentication, privacy-safe operations,
portable export/erasure and a prepared signed release pipeline. Direct internet
exposure is fail-closed until the audited public contract passes and the operator
explicitly acknowledges it. LAN and private-VPN/HTTPS profiles remain supported.

## Supported access profiles

| Profile | Recommended address | Cookie mode | Notes |
|---|---|---|---|
| LAN only | `http://vorrio.lan:9380` | non-Secure | Simple evaluation profile; manual/hardware scans work, but browser camera capture requires HTTPS. |
| Private VPN | `https://vorrio.example.com` | Secure | Preferred remote-access profile when only household devices need access. |
| Public HTTPS | `https://vorrio.example.com` | Secure | Requires the complete internet-exposure security gate. |
| LAN and remote | the same HTTPS hostname inside and outside | Secure | Recommended through split DNS, hairpin routing or a tunnel. |

Using one canonical HTTPS hostname avoids two independent cookie contexts and
is required for a predictable passkey relying-party identity. A raw IP address
should not become the permanent identity of an installation.

Direct LAN HTTP and public HTTPS can be routed to the same container, but this
is not the recommended authenticated setup. With `SESSION_HTTPS_ONLY=true`, a
browser intentionally does not send its session cookie over HTTP. Setting it to
`false` merely to retain HTTP access weakens the public installation.

For a private camera test, an internal CA issued by a maintained reverse proxy
is acceptable after every participating device explicitly trusts that CA. Use
a hostname rather than a raw IP certificate so TLS clients send a predictable
server name. Native store clients will not offer an option to ignore an
untrusted certificate.

## Deployment variables

| Variable | Purpose |
|---|---|
| `PUBLIC_URL` | Optional canonical HTTPS URL for absolute links, passkeys, OAuth callbacks and push metadata. It does not decide which hosts are accepted. |
| `TRUSTED_HOSTS` | Comma-separated hostnames accepted in the HTTP `Host` header. Every deliberate LAN and public hostname belongs here. |
| `FORWARDED_ALLOW_IPS` | IP addresses or networks of reverse proxies whose `X-Forwarded-*` headers may be trusted. Never default to `*` on an exposed port. |
| `ALLOWED_ORIGINS` | Exact browser origins accepted for state changes and passkey ceremonies. The normal PWA remains same-origin; never use a wildcard. |
| `SESSION_HTTPS_ONLY` | Adds the Secure flag to browser session cookies and is mandatory for HTTPS exposure. |
| `PUBLIC_EXPOSURE_ACKNOWLEDGED` | Explicit operator acknowledgement required only after the complete public checklist passes. |
| `PUBLISHED_ADDRESS` | Compose host binding for port 9380; avoid a public bypass around the reverse proxy. |

Example target configuration for one canonical host:

```env
PUBLIC_URL=https://vorrio.example.com
DEPLOYMENT_PROFILE=private_https
TRUSTED_HOSTS=vorrio.example.com
FORWARDED_ALLOW_IPS=172.20.0.0/16
ALLOWED_ORIGINS=https://vorrio.example.com
SESSION_HTTPS_ONLY=true
PUBLIC_EXPOSURE_ACKNOWLEDGED=false
```

If two HTTPS names are intentionally supported, both must be listed:

```env
TRUSTED_HOSTS=vorrio.example.com,vorrio.internal.example.com
ALLOWED_ORIGINS=https://vorrio.example.com,https://vorrio.internal.example.com
```

## Reverse-proxy contract

- use a dedicated hostname, not a stripped path such as `/vorrio`;
- terminate TLS at a maintained reverse proxy or tunnel;
- preserve the original `Host` header;
- replace, rather than append untrusted client values to,
  `X-Forwarded-For`, `X-Forwarded-Proto` and `X-Forwarded-Host`;
- trust forwarded headers only from the actual proxy address or network;
- forward request bodies up to the configured receipt limit;
- keep `/data`, API keys and the container's internal port private;
- verify `/api/health`, login, upload and `/docs` through the public hostname.
- set `PUBLIC_EXPOSURE_ACKNOWLEDGED=true` only after those checks and the
  [external-access security review](EXTERNAL-ACCESS-SECURITY-REVIEW.md).

## Diagnosing HTTP 400

`TrustedHostMiddleware` deliberately returns 400 when the request's
hostname is absent from `TRUSTED_HOSTS`. The fix is to add the real hostname,
not to disable validation globally. Common causes are:

1. only the LAN hostname is allowed but the public domain is used;
2. the reverse proxy replaces `Host` with its internal upstream name;
3. a public web origin tries to call a private LAN origin and triggers browser
   CORS or Private Network Access protection;
4. a proxy address is missing from `FORWARDED_ALLOW_IPS`, causing incorrect
   scheme or redirect generation.

`/api/health` is the liveness check. `/api/readiness` separately reports
database, session-secret, host, proxy, cookie, canonical-URL and exposure-gate
status. An incomplete `public_https` profile returns HTTP 503 for application
traffic; do not bypass that failure by selecting a weaker profile for a public
route.
