import datetime

from odoo import fields
from odoo.tests import TransactionCase


class TestAccountPaymentTermPartnerPaydays(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_term_model = cls.env["account.payment.term"]
        cls.invoice_model = cls.env["account.move"]
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.payment_term_30 = cls.payment_term_model.create(
            {
                "name": "30 days",
                "active": True,
                "line_ids": [
                    fields.Command.create(
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "nb_days": 30,
                        },
                    ),
                ],
            }
        )

    def test_payment_term_without_partner_payment_days(self):
        due_date = self.payment_term_model.apply_payment_days(
            self.payment_term_30.line_ids[0], datetime.date(2025, 5, 1)
        )
        self.assertEqual(due_date, datetime.date(2025, 5, 1))

    def test_payment_term_with_partner_payment_days(self):
        self.partner.write(
            {"customer_payment_days": "5, 15", "supplier_payment_days": "30"}
        )

        due_date = self.payment_term_model.with_context(
            partner_id=self.partner.id, invoice_type="out_invoice"
        ).apply_payment_days(
            self.payment_term_30.line_ids[0], datetime.date(2025, 5, 1)
        )
        self.assertEqual(due_date, datetime.date(2025, 5, 5))

        due_date = self.payment_term_model.with_context(
            partner_id=self.partner.id, invoice_type="out_invoice"
        ).apply_payment_days(
            self.payment_term_30.line_ids[0], datetime.date(2025, 5, 6)
        )
        self.assertEqual(due_date, datetime.date(2025, 5, 15))

        due_date = self.payment_term_model.with_context(
            partner_id=self.partner.id, invoice_type="out_invoice"
        ).apply_payment_days(
            self.payment_term_30.line_ids[0], datetime.date(2025, 5, 26)
        )
        self.assertEqual(due_date, datetime.date(2025, 6, 5))

        due_date = self.payment_term_model.with_context(
            partner_id=self.partner.id, invoice_type="in_invoice"
        ).apply_payment_days(
            self.payment_term_30.line_ids[0], datetime.date(2025, 5, 1)
        )
        self.assertEqual(due_date, datetime.date(2025, 5, 30))
