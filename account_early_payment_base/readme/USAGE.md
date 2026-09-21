Install `account_supplier_early_payment_discount` or
`account_customer_early_payment_discount`; this module does nothing on its
own. Extending modules override `_get_early_payment_values`,
`_early_payment_can_apply` and `_early_payment_adjust_credit_note` for the
move types they handle. A credit note flagged `is_early_payment_refund` is
reconciled with its invoice when posted.
