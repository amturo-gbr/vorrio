# Stripe support integration

Vorrio uses Stripe-hosted Payment Links for financial support. This is the
smallest integration that supports a static website: payment data stays on
Stripe Checkout, the Vorrio website loads no Stripe JavaScript and no secret or
publishable API key is required in the browser.

## Public website boundary

The public Vercel deployment contains five public Stripe destinations: four
hosted Checkout pages and the hosted customer portal. The static site still
loads no Stripe script. `website/support-config.js` contains only public URLs
and is deployed with the website:

```js
window.VORRIO_SUPPORT_LINKS = Object.freeze({
  oneTime: 'https://buy.stripe.com/...',
  monthly5: 'https://buy.stripe.com/...',
  monthly10: 'https://buy.stripe.com/...',
  monthly25: 'https://buy.stripe.com/...',
  portal: 'https://billing.stripe.com/p/login/...',
})
```

`support.js` accepts only HTTPS links on `buy.stripe.com` and
`billing.stripe.com`; invalid targets are hidden. Test links must never be
copied into public website files.

Never put `sk_test_`, `sk_live_`, restricted keys or webhook secrets in this
file, another file under `website/`, Git, screenshots or browser code.

## Current test status

Rechecked on 16 August 2026 against Stripe API `2026-06-24.dahlia`:

- `scripts/setup_stripe_support.mjs` idempotently creates or reuses the
  test-mode Products, four Prices and four Payment Links through Stripe's API;
- the one-time test price accepts a customer-selected EUR amount with a
  EUR 2 minimum and EUR 10 preset;
- the three recurring test prices are fixed at EUR 5, EUR 10 and EUR 25 per
  month;
- all four Stripe-hosted test links are active and return HTTP 200;
- the one-time link creates a paid Stripe invoice with a downloadable PDF;
- the monthly link creates a subscription and first paid invoice;
- the hosted customer portal exposes invoice history, billing details, payment-
  method updates and cancellation at the end of the billing period;
- their test IDs and URLs are stored locally in `.env.stripe.local`, which is
  ignored by Git and must remain private;
- test links remain fully separate from the public live URLs.

The setup script defaults to test mode and accepts only a restricted `rk_test_`
key there. Re-running it returns the existing objects instead of creating
duplicates. A separate read-only integration check validates the current Stripe
sandbox without exposing credentials:

```bash
node scripts/check_stripe_test_support.mjs
```

The complete sandbox rehearsal also passed on 13 August 2026 for the original
EUR 3 one-time and EUR 5 monthly links:

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

On 16 August 2026, the revised hosted pages were checked again through the API
and in desktop and mobile browsers. Stripe rejected EUR 1 with the expected
EUR 2 minimum message, displayed the EUR 10 preset, and rendered each EUR 5,
EUR 10 and EUR 25 monthly tier correctly. No real charge was made.

## Live account audit

The receiving Stripe account was audited on 16 August 2026. Business details
are submitted, charges and payouts are enabled, EUR is the default currency,
there are no outstanding verification requirements, and the statement
descriptor identifies Amturo. Two live Products, four live Prices, four Payment
Links and the hosted customer portal have been created. Amturo branding, the
support address, automatic payment receipts and daily payouts are configured
account-wide.

The public support email, Amturo support URL, Amturo website and Amturo privacy
URL are configured on the shared account.

The account currently contains no active Stripe Tax registration, so
`automatic_tax` deliberately remains disabled. Stripe does not determine the
tax and VAT classification; it must be handled correctly in Amturo UG's annual
accounts.

Create a separate restricted live key with read access to basic account and
business-contact information and read/write access only to Products, Prices,
Payment Links and the customer portal. Keep test and live keys separate. Copy
the private local template, fill it outside Git and run the read-only preflight:

```bash
cp .env.stripe.live.example .env.stripe.live.local
node scripts/setup_stripe_support.mjs --live
```

Without `--apply`, live mode performs account and approval checks and creates
nothing. `--live --apply` is also gate-protected and refuses to create live
objects while any required profile field or approval is missing. Generated live
IDs and URLs remain only in `.env.stripe.live.local`; the public website is not
changed by this script.

## Recommended Stripe account setup

Use the Amturo UG (haftungsbeschränkt) business identity and business payout
account. Before creating live links, verify:

- legal name, address, register and beneficial owners;
- payout bank account and tax details;
- public support email and website privacy/imprint URLs;
- statement descriptor that clearly identifies Amturo;
- account-wide branding that identifies Amturo; Vorrio remains the individual
  Product and Payment Link identity;
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
- Minimum: EUR 2.
- Call to action: payment/support wording, not a charitable-donation promise.
- Collect only the information required for payment, receipts and accounting.

This Stripe pricing model is one-time only; it cannot create recurring payments.

### 2. Optional monthly support

- Type: **Product or subscription**.
- Product: `Vorrio monatlich unterstützen`.
- Fixed tiers: EUR 5, EUR 10 and EUR 25 per month.
- Make cancellation and payment-method management available through Stripe's
  hosted customer portal or the Stripe customer emails.
- Do not promise product-control rights, exclusive security fixes or essential
  self-hosted functionality as a reward.

Each tier has its own Payment Link and shares the same hosted customer portal.

## Test and activation sequence

1. Create all four links in Stripe test mode. **Complete.**
2. Keep test links separate from the public live configuration. **Complete.**
3. Test successful one-time and monthly payments, a failed payment, PDF
   invoices, customer-portal access, recurring cancellation and a refund.
   **Verified in Stripe test mode.**
4. Verify the shared Amturo Checkout branding. **Complete.**
5. Add German and English privacy disclosures. **Complete.**
6. Create the live Products, Prices, Payment Links and portal. **Complete.**
7. Publish only the public live URLs behind guarded controls. **Complete.**
8. Remove `support-config.js` from `.vercelignore`. **Complete.**
9. Run `make website-check` and inspect German and English pages.
10. Test the public links in a signed-out browser before launch.

The public website deliberately needs no Stripe API integration. Local API
automation is used only for repeatable Stripe account setup; visitors still use
Stripe-hosted Payment Links. If Vorrio eventually grants paid benefits or needs
entitlement state, replace this approach with server-created Checkout Sessions
plus signature-verified webhooks.
