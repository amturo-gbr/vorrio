# Release and upgrade policy

## Definition of done

Every change that affects behavior must update the request/response models,
checked-in OpenAPI contract, user/operator documentation and changelog in the
same pull request. `make check` is the mandatory local and CI gate. It runs the
backend suite, frontend build/tests, PWA contract, OpenAPI drift check, guarded
public-HTTPS contract and both isolated acceptance journeys:

```text
first Owner -> catalog/barcode -> synthetic receipt -> local stock
-> budget -> portable export -> operations overview

first login -> onboarding/update note -> invitation -> roles/account block
-> passkey -> TOTP -> recovery code -> password rotation
```

The journey uses a temporary database and synthetic data. It never connects to
or deletes a deployed household.

The complete first-public-release sequence, including GitHub repository
settings and GHCR visibility, is maintained in the
[public launch checklist](PUBLIC-LAUNCH-CHECKLIST.md).

## Container assurance

- Runtime and build base images are pinned by digest.
- CI checks the complete Git history with the digest-pinned Gitleaks CLI before
  building. Only the exact synthetic `YOUR_TOKEN` documentation placeholder is
  allowlisted; findings remain fully redacted in logs.
- CI builds the production Dockerfile, fails for fixed High/Critical findings
  through a digest-pinned official Grype container and creates a CycloneDX JSON
  SBOM through a digest-pinned official Syft container. This avoids runtime
  installer lookups while keeping the scanner and SBOM toolchain immutable. Any VEX
  suppression must live in `security/vex.openvex.json`, include a technical
  reachability justification and be reviewed again on dependency or input-
  format changes.
- Third-party GitHub Actions are pinned to full commit SHAs. Dependabot proposes
  weekly grouped npm, Python, Docker and Actions minor/patch updates for review;
  major upgrades remain deliberate maintainer work so compatibility changes do
  not flood or bypass the release process.
- A `vMAJOR.MINOR.PATCH` tag must match `frontend/package.json` exactly.
- A tag publishes `linux/amd64` and `linux/arm64` images to GHCR with OCI
  labels, BuildKit provenance and SBOM attestation, then keylessly signs the
  immutable digest with Cosign. The same workflow creates the GitHub release
  and attaches the CycloneDX SBOM plus a text file containing the immutable
  image digest.
- The tag workflow repeats `make check` and the fixed High/Critical image gate
  before logging in and publishing, so a tag cannot rely only on a previous
  branch run.

The private 0.8.23 rehearsal produced the first signed multi-architecture image,
SBOM and independent fresh-install proof. Public releases started with 0.8.26.
Version 0.8.27 is the current security-maintenance candidate and receives its
own tag, image, SBOM, signature and fresh-install proof; immutable earlier
assets are never replaced.

## Release rehearsal

Every candidate runs through the same public CI workflow. A maintainer installs
the versioned image with a fresh volume, then repeats source, clean-install,
upgrade/recovery and signature checks before announcing it. Private household
data and the deployed household database are never part of this rehearsal.

## Verify a published image

Use the published owner, repository and version:

```bash
docker pull ghcr.io/amturo-gbr/vorrio:0.8.27
cosign verify \
  --certificate-identity-regexp '^https://github.com/amturo-gbr/vorrio/.github/workflows/release.yml@refs/tags/v' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/amturo-gbr/vorrio:0.8.27
```

Pin production deployments to a version or digest. `latest` is convenient for
evaluation, not an upgrade policy.

## Compatibility and upgrades

- Patch releases may fix defects and security issues without changing the
  documented `/api/v1` contract incompatibly.
- Minor releases may add fields and endpoints; clients must ignore unknown JSON
  fields.
- Breaking API or persisted-data changes require a major version and explicit
  migration notes.
- Back up `/data` and `APP_SECRET_KEY`, read `CHANGELOG.md`, upgrade one version
  at a time when notes require it, then check health, readiness, login, counts
  and the PWA.
- Downgrading a migrated database is unsupported. Restore the matching backup.
