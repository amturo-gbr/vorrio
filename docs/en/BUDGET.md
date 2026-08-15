# Household budget

Vorrio 0.8.14 adds a shared, receipt-based monthly budget under
**Shopping → Budget**. It is deliberately independent of bank accounts and
never presents historic receipt values as live retailer prices.

## Data source and counting rule

A receipt contributes its grand total only when all of these conditions are
true:

- at least one of its lines was explicitly reviewed and committed to Vorrio
  stock;
- its total is present and greater than zero;
- its currency is EUR;
- its purchase date, or the receipt creation date as a fallback, lies in the
  reported period.

An unresolved or merely analyzed receipt cannot change a budget value. A
confirmed receipt without a usable total and a confirmed non-EUR receipt are
reported separately instead of being silently counted. Receipts still awaiting
review are also shown as pending.

This release supports one household per installation. The budget therefore
uses that installation's receipt history and one shared household setting.
Multi-household support requires household ownership on every receipt and
stock domain table before this boundary can be widened safely.

## Metrics

The overview returns:

- confirmed month-to-date spending and counted receipt total;
- remaining monthly budget and percentage used;
- remaining calendar days and a remaining-per-day orientation;
- a simple calendar-pace forecast: `spent / elapsed days × days in month`;
- the same-day cutoff of the previous calendar month;
- up to 24 monthly totals, with six months used by the PWA;
- current-month shares grouped by normalized retailer;
- confirmed, counted, pending, missing-total and other-currency counts.

The forecast is orientation, not a prediction. It does not model payday,
weekends, recurring purchases, holidays or future promotions. When no receipt
has been counted, the PWA shows no forecast value.

## Settings and permissions

Owner and Admin can set one monthly EUR limit between EUR 1 and EUR 1,000,000
and a warning threshold from 50 to 100 percent. Member and Viewer accounts can
read the shared overview but cannot change the target. Removing the target
deletes only the setting; receipts, products, stock and historic summaries stay
untouched.

Browser sessions are required. Scoped automation tokens cannot access or alter
the household budget in 0.8.14. A setting change creates a security audit event
that records the household, configured state and warning percentage, but not
the raw monetary limit.

## REST API

- `GET /api/v1/insights/budget?months=6` returns the overview for 1–24 months.
- `PUT /api/v1/insights/budget/settings` sets or clears the shared target.

The request and response schemas are canonical in the checked-in
[OpenAPI contract](../api/openapi.json) and rendered by `/docs` and `/redoc` on a
running installation.

## Deliberate boundaries

- No bank connector or financial-account data.
- EUR only until currency conversion and household locale rules are explicit.
- No automatic budget target inferred from private receipt history.
- No external live-price comparison until a licensed, authoritative source can
  provide current product, branch, package and availability context.
- No unattended purchase or shopping-list mutation from the budget view.
