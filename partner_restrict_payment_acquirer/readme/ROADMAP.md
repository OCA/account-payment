On 15.0 this module needed an eCommerce companion,
`website_sale_partner_restrict_payment_acquirer`, because the website
checkout's acquirer lookup read the logged-in user's partner instead of taking
one, so a restriction set on the customer being paid for never reached it.

Since 17.0 there is a single funnel —
`payment.provider._get_compatible_providers(company_id, partner_id, amount, …)`
— and `website_sale`'s checkout controller subclasses the `payment.PaymentPortal`
that calls it. The restriction therefore applies to the portal, the backend and
the eCommerce checkout alike, and the companion module has nothing left to do.
`test_the_restriction_follows_the_partner_being_paid_for` is what holds that
true.

The restriction is per provider. Odoo 17.0 also made the payment *method* a
record of its own, so restricting a partner to, say, wire transfer but not card
within one provider is not expressible here and would need a second field.

`sale` is a heavier dependency than the code needs — the model extensions are
`res.partner` and `payment.provider`, and the view targets a group `base`'s own
partner form already has. It is kept as it was on 17.0 because the migration
should not change behaviour; narrowing it to `payment` is a change worth making
on its own, together with the test, which builds a `sale.order` to get a
realistic amount.
