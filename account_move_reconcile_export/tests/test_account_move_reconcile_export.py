# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountMoveReconcileExport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

        # Account receivable
        cls.account_receivable = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                ("account_type", "=", "asset_receivable"),
            ],
            limit=1,
        )
        # Revenue account
        cls.account_revenue = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                ("account_type", "=", "income"),
            ],
            limit=1,
        )
        # Payment journal (bank)
        cls.journal_bank = cls.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", cls.company.id)],
            limit=1,
        )

    def _create_invoice(self, state="draft"):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "account_id": self.account_revenue.id,
                        },
                    )
                ],
            }
        )
        if state == "posted":
            invoice.action_post()
        return invoice

    def _register_payment(self, invoice):
        payment_register = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "payment_date": invoice.invoice_date,
                    "journal_id": self.journal_bank.id,
                    "amount": invoice.amount_total,
                }
            )
        )
        payment_register.action_create_payments()

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_reconciled_move_ids_draft_invoice(self):
        """A draft invoice should have no reconciled moves."""
        invoice = self._create_invoice(state="draft")
        self.assertFalse(invoice.reconciled_move_ids)

    def test_reconciled_move_ids_posted_no_payment(self):
        """A posted invoice with no payment should have no reconciled moves."""
        invoice = self._create_invoice(state="posted")
        self.assertFalse(invoice.reconciled_move_ids)

    def test_reconciled_move_ids_after_payment(self):
        """A posted invoice that has been paid should contain the payment move."""
        invoice = self._create_invoice(state="posted")
        self._register_payment(invoice)
        self.assertTrue(invoice.reconciled_move_ids)
        # The reconciled move should be a payment (not the invoice itself)
        for move in invoice.reconciled_move_ids:
            self.assertNotEqual(move, invoice)
            self.assertEqual(move.move_type, "entry")

    def test_reconciled_move_ids_non_invoice_move(self):
        """A journal entry (non-invoice) should have no reconciled moves."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_revenue.id,
                            "debit": 100.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_receivable.id,
                            "debit": 0.0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        self.assertFalse(move.reconciled_move_ids)

    def test_reconciled_move_ids_multiple_payments(self):
        """Partial payments should each appear in reconciled_move_ids."""
        invoice = self._create_invoice(state="posted")
        # First partial payment
        payment_register = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "payment_date": invoice.invoice_date,
                    "journal_id": self.journal_bank.id,
                    "amount": 60.0,
                }
            )
        )
        payment_register.action_create_payments()
        # Second partial payment
        payment_register2 = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "payment_date": invoice.invoice_date,
                    "journal_id": self.journal_bank.id,
                    "amount": 40.0,
                }
            )
        )
        payment_register2.action_create_payments()
        self.assertEqual(len(invoice.reconciled_move_ids), 2)
