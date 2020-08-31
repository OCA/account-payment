This module makes it possible to use `Slimpay
<https://www.slimpay.com/>`_ as a payment method in Odoo.

If you want to use it on an Odoo shop, you need the
`payment_slimpay_website` module too.

The present module implements the server-to-server transaction with
Slimpay to a SEPA Direct Debit. It integrates nicely with the
`contract_payment_auto` module, provided that a Slimpay payment token
is set on the contract or its partner (see `contract_payment_auto`
module's doc).
