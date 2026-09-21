Companies that grant their customers a discount for paying within a few days
often settle it with a credit note, because a credit note is a fiscal document
the customer can book and, in countries like Mexico, the only way to report a
discount granted after the invoice was issued.

The native early payment discount of the payment terms does not fit that flow:
it writes the discount off when the payment is registered, counts calendar
days only and takes the same percentage off the whole invoice, freight and
insurance included.

This module keeps the percentage and the days of the payment terms and adds:

- **Settle with a credit note**: the customer pays the discounted amount, and
  the discount is granted with a credit note applied to the invoice, so the
  payment receipt reports what was really collected.
- **Business days**: the days to pay within are counted on the working
  calendar of the company, skipping weekends and holidays.
- **Goods only**: the discount leaves out the services of the invoice, such as
  freight or insurance.
- **Approvals**: the credit note is issued in draft, so any approval flow of
  the company (for example `account_move_tier_validation`) can gate it. It is
  reconciled with the invoice as soon as it is posted.
- **Follow-up**: the invoices whose customer paid in time and still wait for
  the credit note show under the *Early Payment to Apply* filter.

The last day to pay, the discount, the credit note and the *Apply Early
Payment* button come from `account_early_payment_base`, shared with the
supplier side (`account_supplier_early_payment_discount`), so both can be
installed together.
