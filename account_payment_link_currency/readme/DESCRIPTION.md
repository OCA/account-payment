This module extends the **Generate a Payment Link** (`payment.link.wizard`)
wizard on customer invoices (`account.move`) to make the payment currency
(`currency_id`) selectable and automatically convert amounts when switching
currencies.

Key features:

- Makes the **Currency** (`currency_id`) field visible and editable in the
  payment link wizard.
- Automatically converts the remaining amount due (`amount_max`), the payment
  amount (`amount`), and open installment previews using the invoice's exact
  exchange rate when switching between the invoice currency and the company
  currency (or the date's exchange rate for other currencies).
- Generates a signed `/payment/pay` link in the selected currency when it
  differs from the invoice currency (e.g., generating a `TRY` payment link for a
  `USD` invoice when the payment provider POS only supports `TRY`).
- Automatically links incoming transactions from `/payment/pay` back to the
  corresponding posted invoice by reference so payment creation and
  cross-currency reconciliation happen automatically upon payment completion.
