<!--
  This is the requirement.md for the "multi-currency-checkout" feature.
  Format guide lives once, at the project root: ../../format.md — read
  that if you're unsure of the syntax; keep this file's markers consistent
  with it.

  The Ticket field is editable straight from the dashboard — typing a
  ticket number into a test case and pressing Enter/clicking away saves it
  back into this exact line via the local write-server, run from the
  project root: `python3 ../../serve.py .` (or `python3 ../../serve.py
  features/multi-currency-checkout` from anywhere). Plain `http.server`
  can view but not save. Editing this file by hand works too.
-->

# CP-1042: Multi-Currency Checkout

> Owner: Priya Nandan | Date: 2026-08-27 | Status: In Review

## Requirements

### REQ-001: Display prices in the customer's local currency
> Priority: High | Status: Approved

The checkout page must detect the customer's locale and display all prices
(item price, shipping, tax, total) in their local currency using the daily
exchange rate published by the finance service. If the locale's currency is
not supported, fall back to USD and show a small notice.

#### Test Cases
- TC-001: Locale with supported currency shows converted prices — Ticket: PAY-2201
  Set browser locale to de-DE, confirm all prices render in EUR using the current daily rate.
- TC-002: Locale with unsupported currency falls back to USD — Ticket: 1212
  Set locale to an unsupported region, confirm USD prices display with the fallback notice.
- TC-003: Exchange rate service is unavailable — Ticket: PAY-3000
  Simulate a timeout from the finance service and confirm the page falls back gracefully instead of erroring.

### REQ-002: Allow currency override at checkout
> Priority: Medium | Status: Approved

The customer can manually switch the displayed currency via a dropdown in
the checkout header. The override persists for the session but does not
change the currency actually charged, which is always settled in USD.

#### Test Cases
- TC-004: Manual currency switch updates displayed prices — Ticket: PAY-2210
  Select GBP from the dropdown, confirm displayed totals update immediately.
- TC-005: Override persists across checkout steps — Ticket: PAY-2211
  Switch currency on step 1, advance to step 2 (payment), confirm the override is still applied. Currently resets to locale default.
- TC-006: Charge amount is unaffected by override — Ticket:
  Confirm the payment gateway receives the USD amount regardless of the displayed currency.

### REQ-003: Show conversion disclaimer on the order confirmation
> Priority: Low | Status: Draft

The order confirmation and email receipt must include a disclaimer stating
that the displayed local-currency amount is an estimate and the actual
charge is settled in USD at the bank's exchange rate.

#### Test Cases
- TC-007: Disclaimer appears on confirmation page — Ticket:
  Blocked on final legal copy for the disclaimer text (see OQ-002).
- TC-008: Disclaimer appears on email receipt — Ticket:
  Same legal copy dependency as TC-007.

### REQ-004: Log currency conversion events for audit
> Priority: Medium | Status: Approved

Every displayed conversion (locale-detected or manual override) must emit
an audit event with the source amount, target currency, rate used, and
timestamp, retained for 7 years per finance compliance.

#### Test Cases
- TC-009: Conversion event is logged on page load — Ticket: PAY-2230
  Load checkout with a non-USD locale, confirm an audit event is emitted with the correct rate.
- TC-010: Conversion event is logged on manual override — Ticket:
  Switch currency manually, confirm a separate audit event is emitted reflecting the override.

## Open Questions

- OQ-001 (Related: REQ-002): Should the currency override persist across sessions (e.g. via a cookie), or reset every visit as currently scoped? — Status: Answered
- OQ-002 (Related: REQ-003): Legal has not yet provided final disclaimer copy — who owns getting this finalized before code freeze? — Status: Answered
- OQ-003 (Related: REQ-001, REQ-004): What is the acceptable staleness window for the daily exchange rate before we consider the finance service "unavailable" and trigger the USD fallback? — Status: Open
- OQ-004 (Related: REQ-001, REQ-004): Do we need a rollback plan if the finance service rate feed changes format? — Status: Open
- OQ-005: Who signs off on the final UX copy? — Status: Open
- OQ-006: test — Status: Open
