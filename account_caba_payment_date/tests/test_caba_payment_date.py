# Copyright 2026 Jarsa (https://www.jarsa.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCabaPaymentDate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.company.tax_exigibility = True
        cls.caba_transition_account = cls.env["account.account"].create(
            {
                "name": "CABA Transition",
                "code": "250199",
                "account_type": "liability_current",
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.caba_tax = cls.env["account.tax"].create(
            {
                "name": "Tax CABA 16%",
                "amount": 16,
                "type_tax_use": "sale",
                "tax_exigibility": "on_payment",
                "cash_basis_transition_account_id": cls.caba_transition_account.id,
                "company_id": cls.company.id,
            }
        )

    def _create_posted_invoice(self, invoice_date):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": invoice_date,
                "date": invoice_date,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1,
                            "price_unit": 1000.0,
                            "tax_ids": [Command.set(self.caba_tax.ids)],
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def _register_payment(self, invoice, payment_date):
        return (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({"payment_date": payment_date})
            ._create_payments()
        )

    def _get_caba_moves(self, invoice):
        return self.env["account.move"].search(
            [("tax_cash_basis_origin_move_id", "=", invoice.id)]
        )

    def test_caba_uses_payment_date(self):
        # The invoice is newer than the payment: standard Odoo would date the
        # cash basis entry on the invoice date (newest reconciled date).
        invoice = self._create_posted_invoice("2026-05-10")
        self._register_payment(invoice, "2026-04-29")
        caba = self._get_caba_moves(invoice)
        self.assertTrue(caba)
        self.assertEqual(caba.mapped("date"), [fields.Date.to_date("2026-04-29")])

    def test_lock_policy_block(self):
        invoice = self._create_posted_invoice("2026-01-15")
        self.company.tax_lock_date = "2026-02-28"
        with self.assertRaises(UserError):
            self._register_payment(invoice, "2026-02-10")

    def test_lock_policy_next_open(self):
        self.company.caba_payment_date_lock_policy = "next_open"
        invoice = self._create_posted_invoice("2026-01-15")
        self.company.tax_lock_date = "2026-02-28"
        self._register_payment(invoice, "2026-02-10")
        caba = self._get_caba_moves(invoice)
        self.assertEqual(caba.mapped("date"), [fields.Date.to_date("2026-03-01")])

    def test_lock_policy_standard(self):
        self.company.caba_payment_date_lock_policy = "standard"
        invoice = self._create_posted_invoice("2026-01-15")
        self.company.tax_lock_date = "2026-02-28"
        self._register_payment(invoice, "2026-02-10")
        caba = self._get_caba_moves(invoice)
        # Standard fallback: Odoo dates the entry out of the locked period
        # (first open month), not on the payment date.
        self.assertTrue(caba.date > fields.Date.to_date("2026-02-28"))
        self.assertNotEqual(caba.date, fields.Date.to_date("2026-02-10"))

    def test_caba_name_follows_new_month(self):
        invoice = self._create_posted_invoice("2026-05-10")
        self._register_payment(invoice, "2026-04-29")
        caba = self._get_caba_moves(invoice)
        self.assertNotIn("/05/", caba.name)
