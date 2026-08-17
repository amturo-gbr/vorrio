# Vorrio language packs

Vorrio keeps translations as data-only language packs. Official packs ship in
the versioned container image and are loaded by the PWA only when selected.
This directory defines the public manifest contract used by official and
community contributions. The complete people, review and promotion workflow is
documented in [Translation community](../docs/en/TRANSLATION-COMMUNITY.md).

## Current status

| Locale | Language | Tier | Runtime status |
|---|---|---|---|
| `de` | Deutsch / German | Official | Included |
| `en` | English | Official | Included |

New work is coordinated through the GitHub **New language** issue form. Drafts
live below `language-packs/community/<locale>/`; their issue is the source of
truth for ownership and reviewer status.

## Package contents

A source package contains exactly:

```text
<locale>/
├── manifest.json
└── translation.json
```

The catalog is a flat JSON object of string keys and string values. Packages
must not contain JavaScript, HTML, styles, binaries or executable hooks.
Interpolation placeholders such as `{{count}}` must be preserved exactly.

Validate a pack before submitting it:

```bash
python3 scripts/validate_language_pack.py path/to/fr
```

Without an argument, the command validates all official catalogs currently
registered in the frontend and every checked-in community candidate.

Create a non-destructive community skeleton with:

```bash
python3 scripts/create_language_pack.py es "Español" "Spanish"
```

The command creates an empty `source-fallback` catalog, derives the minimum
Vorrio version and refuses to replace an existing pack. Contributors add only
the keys they have translated and keep the manifest completion percentage in
sync; CI verifies that percentage.

## Trust levels

- `official`: independently reviewed by fluent speakers, approved by an Amturo
  maintainer, complete across the PWA, server-generated copy, notifications and
  install metadata, and released with the signed Vorrio image;
- `community`: contributor-maintained and reviewable through the dedicated
  GitHub issue and pull-request process. Community status never permits
  executable content and does not by itself make a language selectable.

Vorrio does not install arbitrary remote packages at runtime yet. This is
intentional: the first implementation establishes the versioned, testable
format and lazy-loading boundary. A future administrator-facing installer must
verify an Amturo-controlled package index, checksum, signature, schema version,
Vorrio compatibility and translation completeness before making a package
selectable.

## Adding an official language

1. Add `frontend/src/locales/<locale>/manifest.json` and `translation.json`.
2. Register the lazy catalog import in `frontend/src/locales/registry.ts`.
3. Extend backend locale types and every locale-aware server message.
4. Add a localized PWA manifest.
5. Run `python3 scripts/validate_language_pack.py`, `npm test --prefix frontend`
   and `make check`.
6. Obtain a fluent review of onboarding, authentication, security, deletion,
   stock movement, receipt confirmation and notifications.

Machine translation may prepare a draft but cannot grant official status.
