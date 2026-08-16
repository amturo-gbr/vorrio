# Vorrio engineering policy

Every feature, behavior change and API change is complete only when all affected
documentation is updated in the same change.

Required before completion:

- update user documentation, architecture notes and the changelog;
- update request/response models, endpoint summaries and examples in the
  versioned REST API;
- update both public website languages when the product promise changes, or add
  `- Website impact: none — <concrete reason>` to the changelog;
- regenerate `docs/api/openapi.json` and `docs/en/API.md`;
- run `make check`, including the documentation synchronization check;
- never expose private installation data, credentials, local addresses or
  personal paths in public documentation or examples.

The canonical public API lives under `/api/v1`. Compatibility routes may remain
temporarily, but new integrations must use the versioned paths. Interactive API
documentation is available at `/docs`, ReDoc at `/redoc`, and the
machine-readable contract at `/openapi.json`.

Deployment, authentication or mobile-client changes must also update
`docs/en/DEPLOYMENT-PROFILES.md`, `docs/en/IDENTITY-SECURITY.md`,
`docs/en/MOBILE-APPS.md` and `docs/en/FOUNDATION-CHECKLIST.md` as applicable.
Never hardcode an installation origin into the web client. A canonical URL,
accepted hostnames, trusted proxy networks and CORS origins are separate
security concepts. Do not describe direct internet exposure as supported until
its security gate passes. Native clients must not reuse or extract the browser
session cookie.

Project owner and maintainer: Amturo UG. Source comments and documentation use
ordinary engineering language and contain only information useful to users and
contributors.
