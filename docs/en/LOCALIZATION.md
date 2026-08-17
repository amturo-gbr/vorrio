# Localization

Vorrio ships a complete German and English interface. Language is a personal
account preference, not a household-wide deployment setting. Starting with
0.8.23, each official translation is also a versioned, data-only language pack.
The small German safety fallback remains embedded; other catalogs load on
demand.

## How the language is chosen

Before sign-in, the PWA checks the last local choice and then the browser
language. `en-*` resolves to English, `de-*` to German, and unsupported
languages fall back to German. The first-run and invitation forms send that
choice when they create the account.

After sign-in, the server-side `preferred_locale` of the current account is
authoritative. Changing **Settings → Language & region** stores the choice
through `PATCH /api/v1/auth/preferences`, updates the current screen
immediately and applies on the user's other devices at the next session load.
If saving fails, the PWA restores the previous language and shows the error.

The preference accepts the BCP 47 base values `de` and `en`. It is included in
the authenticated user response, portable export and complete erasure. It is
not available to automation bearer tokens.

## What is localized

- all authenticated and signed-out PWA navigation, forms, dialogs, empty
  states, onboarding, release notes and client-side validation;
- known API errors shown by the PWA, including dynamic scope, stock and
  not-found messages;
- numbers, dates and EUR display through the active browser locale;
- API-token scope descriptions and server-generated Web Push notifications;
- German and English PWA manifests.

Product names, brands, receipt/OCR text, store names and user-entered master
data are household content and are never translated. Vorrio also does not
change the configured deployment timezone or a receipt's recorded currency
when the interface language changes. Third-party error bodies are not exposed;
bounded Vorrio guidance is localized in the PWA instead.

Destructive confirmation phrases are displayed in the active interface
language. The client validates that localized phrase, but sends the stable
canonical confirmation value required by the REST API. This keeps the public
API deterministic without forcing an English user to type German security
copy.

On a brand-new installation, the first Owner's setup language determines the
factory storage locations, units and product groups. These rows are localized
before authenticated catalog editing is possible. They immediately become
normal household data and are never renamed by a later interface-language
change.

## Implementation contract

Every bundled language owns a `manifest.json` and `translation.json` below
`frontend/src/locales/<locale>/`. The central registry in
`frontend/src/locales/registry.ts` supplies the supported locale type, native
label, direction, trust tier, completeness and catalog loader. The PWA embeds
the small German safety fallback, loads another selected language before
rendering and caches that immutable, content-hashed chunk for later offline
starts. Other language chunks are not part of the eager service-worker
precache. If a never-used pack cannot be fetched, the startup remains usable in
German and the account preference is not overwritten.

The original German sentence keys remain a compatibility fallback while they
are migrated gradually. New product copy uses stable namespaced keys such as
`language.interface_label`; CI prevents the number of legacy sentence keys
from increasing. Stable keys must have both German and English values. React
views must use `translate(...)` or `useTranslation()` for visible product copy.

`frontend/src/i18n.ts` owns locale detection, persistence, document direction,
localized manifest selection and number/date/currency formatters. The language
switcher uses each pack's native name instead of translating language names
through the currently active catalog.

The database adds `users.preferred_locale` with a safe `de` default and a
`de`/`en` check. Existing accounts are migrated to German without changing
household, receipt, catalog or stock data. Server-generated personal content
always reads the target user's stored locale; it must never use one process-wide
language.

Run these checks after every UI or localization change:

```bash
cd frontend
npm test
npm run build
cd ..
make pwa-check
python3 scripts/validate_language_pack.py
make api-docs-check
```

`npm test` includes `scripts/check-i18n-contract.mjs`. The contract parses the
TypeScript/TSX sources, fails for a missing or empty English key, requires
German and English singular/plural forms for every count-aware message and
flags likely visible German copy that bypasses the translation layer. The
language-pack validator additionally rejects unexpected files, executable or
HTML content, unknown keys, empty values, changed interpolation placeholders,
invalid metadata and catalogs larger than 2 MiB.

## Official and community packs

Official packs are reviewed, complete and shipped inside the signed Vorrio
container. Users select them directly under **Settings → Language & region**;
there is no separate Docker image or deployment variable. The currently
selected non-default chunk is downloaded from the user's own Vorrio
installation, not a third-party service.

The public data format for future community packs is defined in
`language-packs/schema-v1.json`. A source pack contains only a manifest and a
flat JSON catalog; scripts, HTML, CSS, binary files and install hooks are never
allowed. Community contributions can already use the validator and normal
GitHub review. Runtime installation from a package index remains disabled until
Vorrio can verify an Amturo-controlled index, checksum, signature, compatible
schema/application versions and completeness before exposing a language to
users. Details and contribution steps live in `language-packs/README.md`.
The contributor-facing issue, review, status and official-promotion workflow is
maintained in [Translation community](TRANSLATION-COMMUNITY.md).

## Adding another language

Adding a language is an explicit product and API change, not only a catalog
file. A contribution must update, together:

1. frontend and backend `SupportedLocale` types plus locale detection;
2. a complete reviewed manifest and translation catalog;
3. locale-aware server copy for release notes, token scopes and Push;
4. a localized PWA manifest;
5. setup, invitation, preference, formatting and notification tests;
6. the language-pack validator, this document, OpenAPI, changelog and release
   notes.

Machine translation may prepare a draft, but a fluent reviewer must approve
the complete user journey, especially security, deletion, stock movement and
receipt-confirmation language.
