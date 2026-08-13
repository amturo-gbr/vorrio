## Language pack

- Locale:
- Native / English name:
- Tracking issue: Fixes #
- Contribution stage: requested / in progress / community candidate / official candidate

## Translation evidence

- Translator GitHub handle:
- Independent fluent reviewer GitHub handle:
- Regional variant or terminology notes:
- Machine assistance used: no / yes, described below

Describe any machine-assisted draft and the human review performed. Do not add
personal contact information that does not need to be public.

## Review scope

- [ ] Setup, login, invitations and account recovery were reviewed.
- [ ] Receipt confirmation, stock movement and scanner actions were reviewed.
- [ ] Security warnings, destructive confirmation and privacy text were reviewed.
- [ ] Notifications, plural forms, dates and narrow mobile layouts were reviewed.
- [ ] Product names, brands, retailer text and other household data remain untranslated.
- [ ] An independent fluent reviewer approved the language, or this PR remains a community draft.

## Technical verification

- [ ] The pack contains only `manifest.json` and `translation.json`.
- [ ] `python3 scripts/validate_language_pack.py language-packs/community/<locale>` passes.
- [ ] `make language-pack-check` passes.
- [ ] `make check` passes for an official-language integration.
- [ ] No credentials, receipts, addresses, private hosts or personal paths are included.
- [ ] The changelog and localization/community documentation reflect the new status.

## Contribution certification

- [ ] My commits include `Signed-off-by: Name <email>` as required by the DCO.
- [ ] I agree that this contribution is provided under AGPL-3.0-or-later.
