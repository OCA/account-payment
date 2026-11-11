# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestAccountMoveReconcileExport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal_bank = cls.company_data["default_journal_bank"]
        cls.account_revenue = cls.company_data["default_account_revenue"]
        cls.account_receivable = cls.company_data["default_account_receivable"]

    def _create_test_invoice(self, post=False):
        return self._create_invoice(
            move_type="out_invoice",
            post=post,
            invoice_line_ids=[
                self._prepare_invoice_line(
                    name="Test line",
                    quantity=1,
                    price_unit=100.0,
                    tax_ids=[],
                    account_id=self.account_revenue,
                )
            ],
        )

    def _register_payment(self, invoice, amount=None):
        payment_register = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "payment_date": invoice.invoice_date,
                    "journal_id": self.journal_bank.id,
                    "amount": amount or invoice.amount_total,
                }
            )
        )
        return payment_register._create_payments()

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_reconciled_move_ids_draft_invoice(self):
        """A draft invoice should have no reconciled moves."""
        invoice = self._create_test_invoice()
        self.assertFalse(invoice.reconciled_move_ids)

    def test_reconciled_move_ids_posted_no_payment(self):
        """A posted invoice with no payment should have no reconciled moves."""
        invoice = self._create_test_invoice(post=True)
        self.assertFalse(invoice.reconciled_move_ids)

    def test_reconciled_move_ids_after_payment(self):
        """A posted invoice that has been paid should contain the payment move."""
        invoice = self._create_test_invoice(post=True)
        payment = self._register_payment(invoice)
        self.assertEqual(invoice.reconciled_move_ids, payment.move_id)
        self.assertNotIn(invoice, invoice.reconciled_move_ids)
        self.assertEqual(invoice.reconciled_move_ids.move_type, "entry")

    def test_reconciled_move_ids_non_invoice_move(self):
        """A journal entry (non-invoice) should have no reconciled moves."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.account_revenue.id,
                            "debit": 100.0,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.account_receivable.id,
                            "partner_id": self.partner_a.id,
                            "debit": 0.0,
                            "credit": 100.0,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        self.assertFalse(move.reconciled_move_ids)

    def test_reconciled_move_ids_multiple_payments(self):
        """Partial payments should each appear in reconciled_move_ids."""
        invoice = self._create_test_invoice(post=True)
        payment_1 = self._register_payment(invoice, amount=60.0)
        payment_2 = self._register_payment(invoice, amount=40.0)
        self.assertEqual(
            invoice.reconciled_move_ids,
            payment_1.move_id | payment_2.move_id,
        )
        self.assertEqual(invoice.payment_state, "paid")
