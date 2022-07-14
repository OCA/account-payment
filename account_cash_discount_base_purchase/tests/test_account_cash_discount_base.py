# Copyright 2022 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import Form

from odoo.addons.account_cash_discount_base.tests.common import (
    TestAccountCashDiscountCommon,
)


class TestAccountCashDiscountBase(TestAccountCashDiscountCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Purchase = cls.env["purchase.order"]
        cls.Partner = cls.env["res.partner"]
        cls.Product = cls.env["product.product"]
        cls.partner = cls.Partner.create({"name": "My supplier"})
        cls.product = cls.Product.search([("purchase_ok", "=", True)], limit=1)
        cls.payment_term.write({"discount_percent": 5, "discount_delay": 15})
        with Form(cls.Purchase) as purchase:
            purchase.partner_id = cls.partner
            purchase.payment_term_id = cls.payment_term
            with purchase.order_line.new() as line_form:
                line_form.product_id = cls.product
                line_form.price_unit = 1000
        cls.purchase = purchase.save()
        cls.purchase.button_confirm()

    def create_simple_invoice(self):
        invoice_form = Form(
            self.AccountMove.with_context(
                default_type="in_invoice", default_company_id=self.company.id,
            )
        )
        invoice_form.purchase_vendor_bill_id = self.AccountMove.purchase_vendor_bill_id.search(
            [("purchase_order_id", "=", self.purchase.id)], limit=1
        )
        invoice = invoice_form.save()
        return invoice

    def test_onchange_payment_term(self):
        invoice = self.create_simple_invoice()
        self.assertEqual(invoice.discount_percent, self.payment_term.discount_percent)
        self.assertEqual(invoice.discount_delay, self.payment_term.discount_delay)
