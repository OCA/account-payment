Suppliers often grant a discount when their bills are paid within a few days,
and many of them settle it with a credit note of their own that reaches the
company weeks later, if ever. This module keeps that discount on the supplier
and on its bills, takes it when the bill is paid in time, and follows up the
credit note the supplier owes.

- **Early payment terms on the supplier**: up to two chained discounts, the
  days to pay within, and whether they count from the invoice date or from
  the receipt of the goods.
- **On the vendor bill**: the last day to pay to earn the discount and what
  the discount takes off.
- **Apply Early Payment**: posts an internal credit note for the discount and
  reconciles it with the bill, so what is left to pay is the net amount.
- **Follow-up**: the internal credit note raises a to-do for the *Early
  Payment Credit Notes* activity team, made of the users of the *Follow Up
  Early Payment Credit Notes* group, until the credit note of the supplier
  arrives.

The last day to pay, the discount, the credit note and the *Apply Early
Payment* button come from `account_early_payment_base`, shared with the
customer side (`account_customer_early_payment_discount`).

The native early payment discount of the payment terms does not fit this
flow: it knows a single discount counted from the invoice date and books it as
a write-off when the payment is registered. Here there are two chained
discounts, a base on the receipt date, a credit note because the supplier
issues one, and someone chasing it.
