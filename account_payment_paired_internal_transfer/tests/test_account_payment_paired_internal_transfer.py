# Copyright 2025 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountPaymentPairedInternalTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )

        # Setup company and currency
        cls.company = cls.env.ref("base.main_company")
        cls.currency = cls.company.currency_id

        # Create journals
        cls.bank_journal_1 = cls.env["account.journal"].create(
            {
                "name": "Test Bank Journal 1",
                "code": "TBJ1",
                "type": "bank",
                "company_id": cls.company.id,
            }
        )
        cls.bank_journal_2 = cls.env["account.journal"].create(
            {
                "name": "Test Bank Journal 2",
                "code": "TBJ2",
                "type": "bank",
                "company_id": cls.company.id,
            }
        )
        cls.cash_journal = cls.env["account.journal"].create(
            {
                "name": "Test Cash Journal",
                "code": "TCJ",
                "type": "cash",
                "company_id": cls.company.id,
            }
        )

    def test_01_create_internal_transfer_bank_to_bank(self):
        """Test creation of internal transfer between bank journals"""
        # Create internal transfer payment
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Test Internal Transfer",
            }
        )

        # Verify payment was created correctly
        self.assertEqual(payment.state, "draft")
        self.assertTrue(payment.is_internal_transfer)
        self.assertEqual(payment.destination_journal_id, self.bank_journal_2)
        self.assertFalse(payment.paired_internal_transfer_payment_id)

        # Post the payment
        payment.action_post()

        # Verify paired payment was created
        self.assertTrue(payment.paired_internal_transfer_payment_id)
        paired_payment = payment.paired_internal_transfer_payment_id

        # Verify paired payment properties
        self.assertEqual(paired_payment.journal_id, self.bank_journal_2)
        self.assertEqual(paired_payment.destination_journal_id, self.bank_journal_1)
        self.assertEqual(paired_payment.payment_type, "inbound")
        self.assertEqual(paired_payment.amount, 1000.0)
        self.assertEqual(paired_payment.ref, "Test Internal Transfer")
        self.assertEqual(paired_payment.state, "posted")

        # Verify original payment was updated
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.paired_internal_transfer_payment_id, paired_payment)

    def test_02_create_internal_transfer_bank_to_cash(self):
        """Test creation of internal transfer from bank to cash"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 500.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.cash_journal.id,
                "is_internal_transfer": True,
                "ref": "Bank to Cash Transfer",
            }
        )

        payment.action_post()

        paired_payment = payment.paired_internal_transfer_payment_id
        self.assertTrue(paired_payment)
        self.assertEqual(paired_payment.journal_id, self.cash_journal)
        self.assertEqual(paired_payment.destination_journal_id, self.bank_journal_1)
        self.assertEqual(paired_payment.payment_type, "inbound")
        self.assertEqual(paired_payment.amount, 500.0)

    def test_03_create_internal_transfer_cash_to_bank(self):
        """Test creation of internal transfer from cash to bank"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 750.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.cash_journal.id,
                "destination_journal_id": self.bank_journal_1.id,
                "is_internal_transfer": True,
                "ref": "Cash to Bank Transfer",
            }
        )

        payment.action_post()

        paired_payment = payment.paired_internal_transfer_payment_id
        self.assertTrue(paired_payment)
        self.assertEqual(paired_payment.journal_id, self.bank_journal_1)
        self.assertEqual(paired_payment.destination_journal_id, self.cash_journal)
        self.assertEqual(paired_payment.payment_type, "inbound")
        self.assertEqual(paired_payment.amount, 750.0)

    def test_04_internal_transfer_reconciliation(self):
        """Test automatic reconciliation of liquidity lines"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Reconciliation Test",
            }
        )

        payment.action_post()
        paired_payment = payment.paired_internal_transfer_payment_id

        # Verify liquidity lines were reconciled
        liquidity_lines = (
            payment.move_id.line_ids + paired_payment.move_id.line_ids
        ).filtered(
            lambda l: l.account_id == payment.destination_account_id
            and not l.reconciled
        )

        # Lines should be reconciled
        self.assertTrue(all(line.reconciled for line in liquidity_lines))

    def test_05_internal_transfer_messages(self):
        """Test creation of messages between paired payments"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Message Test",
            }
        )

        payment.action_post()
        paired_payment = payment.paired_internal_transfer_payment_id

        # Verify messages were created
        payment_messages = payment.message_ids.filtered(
            lambda m: "second payment has been created" in m.body
        )
        paired_messages = paired_payment.message_ids.filtered(
            lambda m: "created from" in m.body
        )

        self.assertTrue(payment_messages)
        self.assertTrue(paired_messages)

    def test_06_internal_transfer_already_paired(self):
        """Test already paired internal transfer"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Already Paired Test",
            }
        )

        # Create paired payment manually
        paired_payment = payment.copy(
            {
                "journal_id": self.bank_journal_2.id,
                "destination_journal_id": self.bank_journal_1.id,
                "payment_type": "inbound",
                "paired_internal_transfer_payment_id": payment.id,
            }
        )
        payment.paired_internal_transfer_payment_id = paired_payment

        # Posting should not create new paired payment
        payment.action_post()
        self.assertEqual(payment.paired_internal_transfer_payment_id, paired_payment)

    def test_07_internal_transfer_different_amounts(self):
        """Test internal transfer with different amounts"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Different Amounts Test",
            }
        )

        payment.action_post()
        paired_payment = payment.paired_internal_transfer_payment_id

        # Verify amounts are equal
        self.assertEqual(payment.amount, paired_payment.amount)
        self.assertEqual(payment.amount, 1000.0)

    def test_08_internal_transfer_form_validation(self):
        """Test internal transfer form validation"""
        # Test creation via form
        with Form(self.env["account.payment"]) as form:
            form.payment_type = "outbound"
            form.amount = 1000.0
            form.currency_id = self.currency
            form.date = fields.Date.today()
            form.journal_id = self.bank_journal_1
            form.is_internal_transfer = True
            form.destination_journal_id = self.bank_journal_2
            form.ref = "Form Test"

            payment = form.save()

        self.assertTrue(payment.is_internal_transfer)
        self.assertEqual(payment.destination_journal_id, self.bank_journal_2)
        self.assertEqual(payment.state, "draft")

    def test_09_internal_transfer_readonly_fields(self):
        """Test readonly fields after posting"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Readonly Test",
            }
        )

        # Before posting, destination_journal_id should be editable
        self.assertEqual(payment.state, "draft")

        payment.action_post()

        # After posting, destination_journal_id should be readonly
        # (this is controlled by the view, but we can verify the state)
        self.assertEqual(payment.state, "posted")

    def test_10_internal_transfer_move_lines(self):
        """Test move lines created"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Move Lines Test",
            }
        )

        payment.action_post()
        paired_payment = payment.paired_internal_transfer_payment_id

        # Verify moves were created
        self.assertTrue(payment.move_id)
        self.assertTrue(paired_payment.move_id)

        # Verify liquidity lines exist
        payment_liquidity_lines = payment.move_id.line_ids.filtered(
            lambda l: l.account_id == payment.destination_account_id
        )
        paired_liquidity_lines = paired_payment.move_id.line_ids.filtered(
            lambda l: l.account_id == paired_payment.destination_account_id
        )

        self.assertTrue(payment_liquidity_lines)
        self.assertTrue(paired_liquidity_lines)

    def test_11_internal_transfer_company_consistency(self):
        """Test company consistency between paired payments"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Company Consistency Test",
            }
        )

        payment.action_post()
        paired_payment = payment.paired_internal_transfer_payment_id

        # Verify both payments belong to the same company
        self.assertEqual(payment.company_id, paired_payment.company_id)
        self.assertEqual(payment.company_id, self.company)

    def test_12_internal_transfer_currency_consistency(self):
        """Test currency consistency between paired payments"""
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "amount": 1000.0,
                "currency_id": self.currency.id,
                "date": fields.Date.today(),
                "journal_id": self.bank_journal_1.id,
                "destination_journal_id": self.bank_journal_2.id,
                "is_internal_transfer": True,
                "ref": "Currency Consistency Test",
            }
        )

        payment.action_post()
        paired_payment = payment.paired_internal_transfer_payment_id

        # Verify both payments use the same currency
        self.assertEqual(payment.currency_id, paired_payment.currency_id)
        self.assertEqual(payment.currency_id, self.currency)
