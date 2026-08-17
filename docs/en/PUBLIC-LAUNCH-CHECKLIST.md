# Public launch checklist

This gate is for the first public Amturo release. A successful local build is
necessary but does not by itself publish a repository or container.

## 1. Source and identity

- [ ] The repository is created as `amturo-gbr/vorrio` with no generated README or
  license that could conflict with this source tree.
- [ ] The default branch is `main` and the repository description, topics and
  AGPL-3.0-or-later license are visible.
- [ ] `README.md`, `LICENSE`, `NOTICE`, `AUTHORS.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, support material and the changelog render correctly.
- [ ] No receipt, database, `.env`, API key, cookie, private hostname, LAN
  address, personal path or generated local artifact is staged.
- [ ] Amturo has rechecked the intentionally public company identity, managing
  directors, registered office, register details, phone number and security
  email in both imprint/privacy variants.
- [ ] The full-history secret scan and release-package identity contract pass
  with no unexplained allowlist entry.
- [ ] Immediately after public visibility is enabled and before announcement,
  enable GitHub private vulnerability reporting and verify the advisory link
  from a signed-out browser.

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
- [ ] If private-repository plan restrictions prevented rulesets, create and
  verify the `main` branch ruleset immediately after changing visibility and
  before accepting contributions or announcing the project.
- [ ] Dependency update proposals use the seven-day cooldown and remain grouped
  by ecosystem; major upgrades require deliberate maintainer review.
- [ ] Discussions, issue templates and the support/security routes point users
  to the correct channel.
- [ ] `CODEOWNERS` resolves to an active maintainer; language request and
  language-pack pull-request templates render correctly from a signed-out
  contributor flow.
- [ ] Translation workflow labels (`language:requested`, `language:in-progress`,
  `language:needs-review`, `language:verified`, `language:official`) exist and
  the community guide is linked from README and contribution documentation.
- [ ] German and English complete the same signed-out, onboarding, receipt,
  scanner, catalog, shopping, settings, error and mobile-layout journey; the
  automated i18n contract reports no missing or bypassed copy.
- [ ] Official language manifests and the data-only pack validator pass; no
  runtime community-package source is enabled before signature verification.

## 4. First GHCR publication

- [ ] Push `main` and wait for the CI workflow to pass.
- [ ] Create and push the versioned release tag `v0.8.27` only after CI passes and
  the private release rehearsal is ready for its immutable candidate.
- [ ] Confirm that the release workflow builds `linux/amd64` and `linux/arm64`,
  publishes provenance/SBOM attestations and signs the immutable digest.
- [ ] Confirm that the GHCR package is public, linked to the public repository
  and anonymously pullable after the isolated rehearsal passes.
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
