# Governance

Vorrio is stewarded by Amturo UG. The public roadmap, issue tracker and pull
requests are open, while final release and security decisions remain with the
maintainers.

## Principles

- household data ownership and self-hosting first;
- review before automation changes stock or master data;
- public API and documentation are product features;
- backward compatibility is explicit and time-bounded;
- security fixes are never sponsor-only;
- core features remain available under AGPL-3.0-or-later.

## Contributions

The project uses the Developer Certificate of Origin rather than a contributor
license agreement for normal AGPL development. A CLA is considered only if a
future dual-license model creates a concrete need, and never retroactively.

Translation contributions use the same DCO and license. Amturo approves the
technical boundary and final `community`/`official` tier, while independent
fluent reviewers approve linguistic meaning. A translator cannot be the sole
reviewer of their own official pack. Missing language-review capacity keeps a
pack at community-candidate status instead of blocking safe incremental work or
exposing unverified copy to users. See [Translation community](TRANSLATION-COMMUNITY.md).

## Commercial extensions

Future hosted services or commercial modules use documented network boundaries.
They do not replace the open self-hosted core, and proprietary code is not
loaded as an in-process plugin where that would create ambiguous licensing.
