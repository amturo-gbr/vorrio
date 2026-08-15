# Translation community

Vorrio welcomes data-only language contributions through GitHub. Translators
do not need to run a household server, edit application code or receive access
to an Amturo system. Translation examples and screenshots must use synthetic
data.

## Contribution stages

| Stage | Meaning | Selectable in Vorrio |
|---|---|---|
| Requested | An issue records interest, locale and possible contributors. | No |
| In progress | A contributor owns a draft under `language-packs/community/`. | No |
| Community candidate | The data-only pack passes technical checks and can be reviewed incrementally. | No |
| Verified community | Complete catalog with independent fluent review, awaiting product integration. | No |
| Official | Integrated across frontend, backend, notifications and install metadata, then shipped in a signed Vorrio release. | Yes |

Community status is not a lower security mode. Every pack is still plain JSON
and must pass the same content, size and placeholder rules. It only describes
translation completeness and review maturity.

## Start a language

1. Search open issues for the locale and open the **New language** issue when
   none exists. One issue coordinates translators and independent reviewers.
2. Fork the repository, create a branch and generate the package skeleton:

   ```bash
   python3 scripts/create_language_pack.py es "Español" "Spanish"
   ```

   Use `--direction rtl` for a right-to-left language or a regional BCP 47 tag
   such as `pt-BR` when terminology genuinely differs.
3. Add translations to
   `language-packs/community/<locale>/translation.json`. The English catalog at
   `frontend/src/locales/en/translation.json` is the canonical source. Missing
   community entries deliberately fall back to English while the draft is
   outside the runtime.
4. Update `completion` in `manifest.json` to the rounded percentage of canonical
   keys explicitly present. The validator rejects an inaccurate percentage.
5. Run:

   ```bash
   python3 scripts/validate_language_pack.py language-packs/community/es
   make language-pack-check
   ```

6. Commit with DCO sign-off and open a pull request using the **Language pack**
   template. Link the language issue and disclose any machine-assisted draft.

The generator refuses to replace an existing directory. A pack contains only
`manifest.json` and `translation.json`; images, scripts, styles, binaries and
install hooks are rejected.

## Review responsibilities

| Responsibility | Translator | Fluent reviewer | Amturo maintainer | Automation |
|---|---:|---:|---:|---:|
| Translate and explain regional terminology | Yes | Reviews | Observes | No |
| Check natural language and household vocabulary | Self-review | Yes | Verifies evidence | No |
| Check login, security, deletion and stock meaning | Self-review | Yes | Requires review | Structural checks |
| Validate JSON, placeholders, files and completeness | Optional locally | Optional locally | Confirms CI | Yes |
| Decide community or official status | Proposes | Recommends | Yes | No |
| Merge, integrate and publish a signed release | No | No | Yes | Required gates |

Official status requires a technical maintainer approval and at least one
independent fluent reviewer who did not author the full translation. Security,
recovery, destructive deletion, receipt confirmation and stock movement copy
receives a second independent language check before release. If reviewers are
not available, a technically valid pack can remain a community candidate
without being exposed to users.

Machine translation may prepare a disclosed draft. It cannot act as a reviewer
or grant verified or official status.

## Maintainer workflow

Maintainers apply or create these issue/PR labels:

- `language:requested`
- `language:in-progress`
- `language:needs-review`
- `language:verified`
- `language:official`

Before merging a community candidate, confirm the issue is linked, DCO sign-off
is present, the specialized checklist is complete and CI validates the pack.
Merging the data-only candidate does not make it selectable.

Promotion to official is a separate product pull request. It registers the
locale, completes locale-aware backend messages and notifications, adds PWA
install metadata, updates tests and documentation, and passes `make check`.
The official pack becomes available only in the next signed image. Arbitrary
runtime downloads remain disabled until Vorrio has a signed, checksummed and
version-compatible Amturo package index.

Git history and release notes credit contributors. Translation packs do not
carry executable attribution or personal metadata, and contributors should not
publish email addresses beyond the DCO identity they intentionally use.

All contributions follow the [Code of Conduct](https://github.com/amturo-gbr/vorrio/blob/main/CODE_OF_CONDUCT.md),
[contribution guide](https://github.com/amturo-gbr/vorrio/blob/main/CONTRIBUTING.md),
[governance](GOVERNANCE.md) and the
[language-pack contract](https://github.com/amturo-gbr/vorrio/blob/main/language-packs/README.md).
