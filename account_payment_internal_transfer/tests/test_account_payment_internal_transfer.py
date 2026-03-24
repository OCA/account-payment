# Copyright 2026 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountPaymentInternalTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.transfer_account = cls.company.transfer_account_id
        cls.outstanding_account = cls.env["account.account"].create(
            {
                "name": "Outstanding Payments",
                "code": "XOUT",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        cls.bank_journal_1 = cls.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", cls.company.id)], limit=1
        )
        if not cls.bank_journal_1:
            cls.bank_journal_1 = cls.env["account.journal"].create(
                {
                    "name": "Bank 1",
                    "type": "bank",
                    "code": "BNK1",
                    "company_id": cls.company.id,
                }
            )
        cls.bank_journal_2 = cls.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("company_id", "=", cls.company.id),
                ("id", "!=", cls.bank_journal_1.id),
            ],
            limit=1,
        )
        if not cls.bank_journal_2:
            cls.bank_journal_2 = cls.env["account.journal"].create(
                {
                    "name": "Bank 2",
                    "type": "bank",
                    "code": "BNK2",
                    "company_id": cls.company.id,
                }
            )
        for journal in cls.bank_journal_1 | cls.bank_journal_2:
            for method_line in (
                journal.inbound_payment_method_line_ids
                | journal.outbound_payment_method_line_ids
            ):
                method_line.payment_account_id = cls.outstanding_account

    def _create_transfer(self, amount=1000.0):
        return self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": amount,
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
            }
        )

    def test_internal_transfer_full_flow(self):
        payment = self._create_transfer()
        self.assertTrue(payment.is_internal_transfer)
        self.assertEqual(payment.destination_account_id, self.transfer_account)
        self.assertFalse(payment.paired_internal_transfer_payment_id)
        payment.action_post()
        paired = payment.paired_internal_transfer_payment_id
        self.assertTrue(paired)
        self.assertEqual(paired.journal_id, self.bank_journal_2)
        self.assertEqual(paired.destination_journal_id, self.bank_journal_1)
        self.assertEqual(paired.amount, 1000.0)
        self.assertEqual(paired.payment_type, "inbound")
        self.assertTrue(paired.is_internal_transfer)
        self.assertEqual(paired.paired_internal_transfer_payment_id, payment)
        self.assertTrue(payment.move_id)
        self.assertTrue(paired.move_id)
        lines_1 = payment.move_id.line_ids
        self.assertEqual(len(lines_1), 2)
        debit_1 = lines_1.filtered(lambda line: line.debit > 0)
        credit_1 = lines_1.filtered(lambda line: line.credit > 0)
        self.assertEqual(debit_1.account_id, self.transfer_account)
        self.assertEqual(credit_1.account_id, payment.outstanding_account_id)

        lines_2 = paired.move_id.line_ids
        self.assertEqual(len(lines_2), 2)
        debit_2 = lines_2.filtered(lambda line: line.debit > 0)
        credit_2 = lines_2.filtered(lambda line: line.credit > 0)
        self.assertEqual(debit_2.account_id, paired.outstanding_account_id)
        self.assertEqual(credit_2.account_id, self.transfer_account)
        transfer_lines = (lines_1 + lines_2).filtered(
            lambda line: line.account_id == self.transfer_account
        )
        self.assertEqual(len(transfer_lines), 2)
        self.assertTrue(all(line.reconciled for line in transfer_lines))

    def test_cancel_cascades_to_paired_payment(self):
        payment = self._create_transfer()
        payment.action_post()
        paired = payment.paired_internal_transfer_payment_id
        payment.action_cancel()
        self.assertEqual(payment.state, "canceled")
        self.assertEqual(paired.state, "canceled")
        self.assertEqual(payment.move_id.state, "cancel")
        self.assertEqual(paired.move_id.state, "cancel")

    def test_cancel_from_paired_side_cascades_back(self):
        payment = self._create_transfer()
        payment.action_post()
        paired = payment.paired_internal_transfer_payment_id
        paired.action_cancel()
        self.assertEqual(payment.state, "canceled")
        self.assertEqual(paired.state, "canceled")

    def test_draft_cascades_to_paired_payment(self):
        payment = self._create_transfer()
        payment.action_post()
        paired = payment.paired_internal_transfer_payment_id
        payment.action_cancel()
        payment.action_draft()
        self.assertEqual(payment.state, "draft")
        self.assertEqual(paired.state, "draft")

    def test_draft_from_paired_side_cascades_back(self):
        payment = self._create_transfer()
        payment.action_post()
        paired = payment.paired_internal_transfer_payment_id
        paired.action_cancel()
        paired.action_draft()
        self.assertEqual(payment.state, "draft")
        self.assertEqual(paired.state, "draft")

    def test_unlink_draft_never_posted_cascades(self):
        payment = self._create_transfer(amount=750.0)
        payment_id = payment.id
        payment.unlink()
        self.assertFalse(self.env["account.payment"].search([("id", "=", payment_id)]))

    def test_unlink_non_draft_raises_error(self):
        payment = self._create_transfer(amount=500.0)
        payment.action_post()
        with self.assertRaises(UserError):
            payment.unlink()

    def test_unlink_canceled_raises_error(self):
        payment = self._create_transfer()
        payment.action_post()
        payment.action_cancel()
        with self.assertRaises(UserError):
            payment.unlink()

    def test_regular_payment_not_affected(self):
        vendor = self.env["res.partner"].create({"name": "Test Vendor"})
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "partner_type": "supplier",
                "partner_id": vendor.id,
                "amount": 100.0,
                "journal_id": self.bank_journal_1.id,
            }
        )
        self.assertFalse(payment.is_internal_transfer)
        payment.action_post()
        self.assertFalse(payment.paired_internal_transfer_payment_id)
        payment.action_cancel()
        self.assertEqual(payment.state, "canceled")
        payment.action_draft()
        self.assertEqual(payment.state, "draft")

    def test_button_open_paired_payment(self):
        payment = self._create_transfer(amount=500.0)
        payment.action_post()
        paired = payment.paired_internal_transfer_payment_id
        action = payment.button_open_paired_payment()
        self.assertEqual(action["res_model"], "account.payment")
        self.assertEqual(action["res_id"], paired.id)
        self.assertEqual(action["view_mode"], "form")
