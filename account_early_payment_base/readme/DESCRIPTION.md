Technical module shared by the early payment discounts settled by a credit
note: `account_supplier_early_payment_discount` (vendor bills) and
`account_customer_early_payment_discount` (customer invoices). It holds, on
`account.move`, the last day to pay, the amount of the discount, the credit
note that settles it and the *Apply Early Payment* button, plus the business
day helpers of `res.company`, so both modules can be installed together.
