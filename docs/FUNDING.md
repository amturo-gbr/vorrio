# Funding Vorrio

Vorrio is open-source software maintained by Amturo UG. Funding should support
maintenance, security work, documentation, community support and public build
infrastructure without reducing the self-hosted core.

## Planned first option: Stripe Payment Links

Stripe Payment Links is the preferred launch option. The static website links
to Stripe-hosted Checkout and does not load Stripe JavaScript or expose an API
key. This keeps the website dependency-free and avoids contacting Stripe until
the visitor actively chooses financial support.

The prepared website supports two independent links:

- a one-time payment where the supporter chooses the amount;
- an optional fixed monthly sponsorship.

Both controls stay hidden while their values in `website/support-config.js` are
empty. See `docs/STRIPE-SUPPORT.md` for the account, link and activation steps.

Two Stripe test-mode links are now prepared: customer-selected one-time support
with a EUR 3 minimum and EUR 10 preset, and fixed support at EUR 5 per month.
Both hosted pages are reachable, but neither test link is placed on the public
website. The idempotent setup is in
`scripts/setup_stripe_test_support.mjs`; local keys, IDs and test URLs remain in
the Git-ignored `.env.stripe.local` file.

The sandbox rehearsal covers successful one-time and monthly card payments,
downloadable PDF invoices, a declined payment, the hosted customer portal,
subscription cancellation at period end and a full refund. Stripe chooses the
available payment methods dynamically, so the live account must be checked
again before launch rather than promising a fixed public method list.

## Verified current status

Checked on 13 August 2026: `amturo-gbr/vorrio` is the canonical repository and
is still private; the public `amturo-gbr` organization currently exposes no
public repositories. Neither `@amturo-gbr` nor `@adrian-amturo` has applied to
join GitHub Sponsors. No `.github/FUNDING.yml` exists, which is intentional
while GitHub Sponsors is deferred. All GitHub Sponsors wording and controls are
hidden from the project website.

Rewards must not delay security fixes or make essential self-hosted features
exclusive. Sponsor logos and public names are opt-in.

## Later options

Open Collective is useful if the community wants a public budget and expense
ledger. Because Amturo UG is already a legal entity, an independent collective
or direct accounting may be simpler than a fiscal host; accounting advice is
required before activation.

## Wording and taxes

Financial support to a commercial UG is not presented as a tax-deductible
charitable donation, and Vorrio does not promise donation receipts. Public copy
uses “support” or “sponsorship”. Amturo UG records payouts and applicable taxes
through its normal accounting process.

No live payment link is publicly active in 0.8.25. Stripe support is activated
only after the receiving Amturo account, live Payment Links, legal copy and
bookkeeping process are ready. Stripe secret keys never belong in `website/` or
a browser bundle.

## Website activation sequence

The static project website keeps financial support unavailable until all launch
gates are complete:

1. complete and verify the Amturo Stripe business account, payout account and
   tax details;
2. approve the public sponsorship wording, VAT treatment and bookkeeping flow;
3. create the one-time and optional monthly Stripe Payment Links in test mode
   (**prepared**);
4. verify checkout, PDF invoices, a failed payment, the customer portal,
   refunds and subscription cancellation (**verified in test mode**);
5. create the live links and add only their public `buy.stripe.com` URLs to
   `website/support-config.js`;
6. verify both languages and payment flows from a signed-out browser.

PayPal is not the launch default. A standalone PayPal button would add another
checkout, reconciliation and legal-copy path without improving the source-to-
support flow already provided by Stripe. It may be reconsidered later
only when supporters demonstrably need it and Amturo has approved the business
account, fees, refunds, privacy wording and accounting treatment. Open
Collective remains a later transparency option if Vorrio develops a community
budget that benefits from a public income and expense ledger.
