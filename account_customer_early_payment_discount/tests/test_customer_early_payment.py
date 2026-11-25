# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCustomerEarlyPayment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # Monday to Friday, with the 16th of September off.
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "Business days", "company_id": cls.company.id}
        )
        cls.env["resource.calendar.leaves"].create(
            {
                "name": "Holiday",
                "calendar_id": cls.calendar.id,
                "date_from": "2026-09-16 00:00:00",
                "date_to": "2026-09-16 23:59:59",
            }
        )
        cls.company.resource_calendar_id = cls.calendar
        cls.term = cls.env["account.payment.term"].create(
            {
                "name": "3% in 8 business days",
                "early_discount": True,
                "discount_percentage": 3.0,
                "discount_days": 8,
                "early_discount_credit_note": True,
                "early_discount_business_days": True,
                "early_discount_goods_only": True,
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 100, "nb_days": 30}
                    )
                ],
            }
        )
        cls.tax = cls.env["account.tax"].create(
            {"name": "VAT 16%", "amount": 16.0, "type_tax_use": "sale"}
        )
        cls.goods = cls.env["product.product"].create(
            {"name": "Helmet", "type": "consu", "taxes_id": [Command.set(cls.tax.ids)]}
        )
        cls.service = cls.env["product.product"].create(
            {
                "name": "Freight",
                "type": "service",
                "taxes_id": [Command.set(cls.tax.ids)],
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Early Payer"})
        # The payment must reduce the balance of the invoice right away.
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", cls.company.id)], limit=1
        )
        outstanding = cls.env["account.account"].create(
            {
                "name": "Outstanding Receipts",
                "code": "EPDOUT",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        cls.journal.inbound_payment_method_line_ids.payment_account_id = outstanding

    def _invoice(self, term=None, invoice_date="2026-09-11"):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.customer.id,
                "invoice_date": invoice_date,
                "invoice_payment_term_id": (term or self.term).id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.goods.id,
                            "quantity": 10,
                            "price_unit": 100.0,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.service.id,
                            "quantity": 1,
                            "price_unit": 200.0,
                        }
                    ),
                ],
            }
        )
        invoice.action_post()
        return invoice

    def _pay(self, invoice, amount, payment_date):
        wizard = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({"amount": amount, "payment_date": payment_date})
        )
        return wizard._create_payments()

    def test_date_and_amount(self):
        invoice = self._invoice()
        # Friday the 11th + 8 business days, skipping the holiday of the 16th.
        self.assertEqual(invoice.early_payment_date, date(2026, 9, 24))
        # 3% of the goods with their tax (1,160), the freight left out.
        self.assertEqual(invoice.early_payment_amount, 34.80)
        self.assertEqual(invoice.amount_total, 1392.0)
        self.assertFalse(invoice.early_payment_state)
        # The native write-off is off: the customer owes the full amount.
        receivable = invoice.line_ids.filtered(
            lambda line: line.account_type == "asset_receivable"
        )
        self.assertFalse(receivable.discount_date)
        wizard = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({})
        )
        self.assertFalse(wizard.early_payment_discount_mode)
        self.assertEqual(wizard.amount, 1392.0)

    def test_calendar_days_whole_invoice(self):
        self.term.write(
            {"early_discount_business_days": False, "early_discount_goods_only": False}
        )
        invoice = self._invoice()
        self.assertEqual(invoice.early_payment_date, date(2026, 9, 19))
        self.assertEqual(invoice.early_payment_amount, 41.76)

    def test_apply(self):
        invoice = self._invoice()
        self._pay(invoice, 1357.20, "2026-09-24")
        self.assertEqual(invoice.early_payment_state, "available")
        action = invoice.action_apply_early_payment()
        credit_note = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(invoice.early_payment_credit_note_id, credit_note)
        self.assertEqual(invoice.early_payment_state, "applied")
        self.assertEqual(credit_note.state, "draft")
        self.assertTrue(credit_note.is_early_payment_refund)
        self.assertEqual(credit_note.reversed_entry_id, invoice)
        self.assertEqual(credit_note.invoice_line_ids.product_id, self.goods)
        self.assertEqual(credit_note.amount_total, 34.80)
        with self.assertRaises(UserError):
            invoice.action_apply_early_payment()
        credit_note.action_post()
        self.assertEqual(invoice.amount_residual, 0.0)
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))
        self.assertTrue(credit_note.line_ids.filtered("reconciled"))

    def test_cancelled_credit_note_frees_the_discount(self):
        invoice = self._invoice()
        self._pay(invoice, 1357.20, "2026-09-24")
        invoice.action_apply_early_payment()
        invoice.early_payment_credit_note_id.button_cancel()
        self.assertEqual(invoice.early_payment_state, "available")

    def test_paid_late(self):
        invoice = self._invoice()
        self._pay(invoice, 1357.20, "2026-09-25")
        self.assertFalse(invoice.early_payment_state)
        with self.assertRaises(UserError):
            invoice.action_apply_early_payment()

    def test_paid_too_little(self):
        invoice = self._invoice()
        self._pay(invoice, 1000.0, "2026-09-14")
        self.assertFalse(invoice.early_payment_state)
        self._pay(invoice, 357.20, "2026-09-24")
        self.assertEqual(invoice.early_payment_state, "available")

    def test_other_terms_untouched(self):
        term = self.env["account.payment.term"].create(
            {
                "name": "Native 2/7",
                "early_discount": True,
                "discount_percentage": 2.0,
                "discount_days": 7,
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 100, "nb_days": 30}
                    )
                ],
            }
        )
        invoice = self._invoice(term=term)
        self.assertFalse(invoice.early_payment_date)
        receivable = invoice.line_ids.filtered(
            lambda line: line.account_type == "asset_receivable"
        )
        self.assertEqual(receivable.discount_date, date(2026, 9, 18))
