A posted vendor bill of a supplier with early payment terms shows the last day
to pay and the discount. Press *Apply Early Payment*: an internal credit note
for the discount is posted and reconciled with the bill, and a to-do for the
credit note the supplier owes goes to the follow-up team, on that internal
credit note. Close it when the credit note of the supplier arrives.

The business day the discount is paid on is exposed through
`account.move._early_payment_pay_date()`: the early payment date itself, or
the business day before when it falls on a weekend or a holiday of the
working calendar of the company. Payment order integration lives in
`account_payment_order_early_payment_discount` (OCA/bank-payment).
