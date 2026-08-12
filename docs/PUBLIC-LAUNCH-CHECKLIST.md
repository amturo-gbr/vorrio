# Public launch checklist

This gate is for the first public Amturo release. A successful local build is
necessary but does not by itself publish a repository or container.

## 1. Source and identity

- [ ] The repository is created as `amturo/vorrio` with no generated README or
  license that could conflict with this source tree.
- [ ] The default branch is `main` and the repository description, topics and
  AGPL-3.0-or-later license are visible.
- [ ] `README.md`, `LICENSE`, `NOTICE`, `AUTHORS.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, support material and the changelog render correctly.
- [ ] No receipt, database, `.env`, API key, cookie, private hostname, LAN
  address, personal path or generated local artifact is staged.
- [ ] GitHub private vulnerability reporting is enabled before issues are
  opened to the public.

## 2. Release candidate

- [ ] `make check` passes from a clean checkout.
- [ ] The automated documentation-link and release-package hygiene checks pass;
  the latter sees exactly the tracked and unignored files intended for GitHub.
- [ ] The release tag exactly matches `frontend/package.json`.
- [ ] Desktop and 390 px mobile UAT cover setup/login, all five navigation
  areas, scanner actions, receipt review, catalog/count review, shopping tabs,
  settings feedback and logout without console errors.
- [ ] Destructive privacy actions run only against the synthetic launch-smoke
  database.
- [ ] The production image has no fixed High or Critical vulnerability finding;
  every VEX statement still has a current reachability justification.
- [ ] A CycloneDX SBOM is generated and the image runs as the unprivileged
  application user with a persistent `/data` volume.

## 3. GitHub controls

- [ ] CI is required for pull requests to `main`.
- [ ] Direct force-push and branch deletion are blocked.
- [ ] Dependabot security and version updates are enabled.
- [ ] Secret scanning and push protection are enabled where the GitHub plan
  supports them.
- [ ] Discussions, issue templates and the support/security routes point users
  to the correct channel.

## 4. First GHCR publication

- [ ] Push `main` and wait for the CI workflow to pass.
- [ ] Create and push the signed release tag `v0.8.18` only after CI passes.
- [ ] Confirm that the release workflow builds `linux/amd64` and `linux/arm64`,
  publishes provenance/SBOM attestations and signs the immutable digest.
- [ ] Change the GHCR package visibility to public and link it to the public
  repository if GitHub did not inherit those settings automatically.
- [ ] Pull the versioned image on a second machine and complete first setup with
  a fresh volume.
- [ ] Verify the signature and health/readiness endpoints using the commands in
  [Release and upgrade policy](RELEASES.md).

## 5. Installation and recovery proof

- [ ] Test both source-build Compose and the published GHCR Compose example.
- [ ] Verify LAN-only defaults, private HTTPS/PWA installation and the guarded
  public-HTTPS profile separately.
- [ ] Back up `/data` and `APP_SECRET_KEY`, restore them into a fresh container,
  and compare login, product, receipt and stock counts.
- [ ] Confirm the upgrade notes, downgrade warning and support boundary in the
  public release notes.

## 6. Post-release

- [ ] Open the public README, API documentation, container page and generated
  release from a signed-out browser.
- [ ] Install the exact published digest once and repeat the launch smoke.
- [ ] Record the released digest, CI run and SBOM artifact in the release notes.
- [ ] Announce only after installation, signature verification and first-login
  recovery have all passed.

The maintainer checks every box against public or synthetic data. A private
household installation is never used as release evidence and does not need a
public Cloudflare route.
