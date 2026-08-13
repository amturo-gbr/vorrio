# Stripe support integration

Vorrio uses Stripe-hosted Payment Links for financial support. This is the
smallest integration that supports a static website: payment data stays on
Stripe Checkout, the Vorrio website loads no Stripe JavaScript and no secret or
publishable API key is required in the browser.

## Public website boundary

The public Vercel deployment contains no Stripe controls, Stripe copy or Stripe
runtime code. `website/.vercelignore` excludes the local placeholder
`website/support-config.js`, whose two empty URL slots are reserved for a later
activation change:

```js
window.VORRIO_SUPPORT_LINKS = Object.freeze({
  oneTime: '',
  monthly: '',
})
```

The placeholder is not referenced by public HTML or JavaScript. Activating
payments requires one reviewed change that adds the live controls and strict
`https://buy.stripe.com/` URL validation, removes the Vercel exclusion, updates
the privacy policy and verifies both languages. Test links must never be copied
into public website files.

Never put `sk_test_`, `sk_live_`, restricted keys or webhook secrets in this
file, another file under `website/`, Git, screenshots or browser code.

## Current test status

Prepared on 13 August 2026:

- `scripts/setup_stripe_test_support.mjs` idempotently creates or reuses the
  two test-mode Products, Prices and Payment Links through Stripe's API;
- the one-time test price accepts a customer-selected EUR amount with a
  EUR 3 minimum and EUR 10 preset;
- the recurring test price is fixed at EUR 5 per month;
- both Stripe-hosted test links are active and return HTTP 200;
- the one-time link creates a paid Stripe invoice with a downloadable PDF;
- the monthly link creates a subscription and first paid invoice;
- the hosted customer portal exposes invoice history, billing details, payment-
  method updates and cancellation at the end of the billing period;
- their test IDs and URLs are stored locally in `.env.stripe.local`, which is
  ignored by Git and must remain private;
- `website/support-config.js` remains empty and is excluded from Vercel, so test
  links and inactive payment wording cannot appear on the public website.

The setup script only accepts a restricted `rk_test_` key and refuses live
mode. Re-running it must return the existing objects instead of creating
duplicates.

The complete sandbox rehearsal also passed on 13 August 2026:

- a EUR 10 one-time card payment completed successfully;
- a EUR 5 monthly card subscription completed successfully;
- Stripe produced downloadable PDF invoices for both successful flows;
- a declined test card remained unsuccessful and created no paid transaction;
- the monthly subscription was cancelled in the hosted portal and now ends at
  the close of its current billing period;
- the one-time payment was refunded in full and is shown as refunded in the
  Stripe Dashboard.

Checkout displayed Stripe's dynamic payment-method selection rather than a
hard-coded list. The exact methods vary by supporter, browser, device, currency
and Stripe account eligibility and must therefore be rechecked in live mode.

## Recommended Stripe account setup

Use the Amturo UG (haftungsbeschränkt) business identity and business payout
account. Before creating live links, verify:

- legal name, address, register and beneficial owners;
- payout bank account and tax details;
- public support email and website privacy/imprint URLs;
- statement descriptor that clearly identifies Amturo or Vorrio;
- branding with the Vorrio logo and `#176B35` accent colour;
- automatic receipts, refund handling and relevant payment methods;
- Stripe data-processing terms and the internal bookkeeping workflow.

The final tax and VAT treatment of commercial sponsorship income must be agreed
with Amturo's tax adviser before activation. Public wording uses “support” or
“sponsorship”, not a promise of a tax-deductible donation or donation receipt.

## Prepared Payment Links

### 1. One-time support

- Type: **Customers choose what to pay**.
- Title: `Vorrio einmalig unterstützen`.
- Suggested amount: EUR 10.
- Suggested minimum: EUR 3.
- Call to action: payment/support wording, not a charitable-donation promise.
- Collect only the information required for payment, receipts and accounting.

This Stripe pricing model is one-time only; it cannot create recurring payments.

### 2. Optional monthly support

- Type: **Product or subscription**.
- Product: `Vorrio monatlich unterstützen`.
- Initial fixed price: EUR 5 per month.
- Make cancellation and payment-method management available through Stripe's
  hosted customer portal or the Stripe customer emails.
- Do not promise product-control rights, exclusive security fixes or essential
  self-hosted functionality as a reward.

Additional monthly tiers can be added later if real demand justifies the extra
copy and accounting complexity.

## Test and activation sequence

1. Create both links in Stripe test mode. **Prepared.**
2. Keep `website/support-config.js` empty and excluded from Vercel while testing
   the links directly. **Verified.**
3. Test successful one-time and monthly payments, a failed payment, PDF
   invoices, customer-portal access, recurring cancellation and a refund.
   **Verified in Stripe test mode.**
4. Confirm the privacy text, terms and accounting process.
5. Create or activate the live Payment Links.
6. Add only the two live `https://buy.stripe.com/...` URLs together with guarded
   public controls and the corresponding German and English privacy disclosure.
7. Remove `support-config.js` from `.vercelignore` only in that reviewed change.
8. Run `make website-check` and inspect German and English pages.
9. Test the public links in a signed-out browser before launch.

The public website deliberately needs no Stripe API integration. Local API
automation is used only for repeatable Stripe account setup; visitors still use
Stripe-hosted Payment Links. If Vorrio eventually grants paid benefits or needs
entitlement state, replace this approach with server-created Checkout Sessions
plus signature-verified webhooks.
