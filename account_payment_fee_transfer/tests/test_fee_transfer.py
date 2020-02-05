# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import SingleTransactionCase


class TestFeeTransfer(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal_model = cls.env["account.journal"]
        cls.payment_model = cls.env["account.payment"]
        cls.account_model = cls.env["account.account"]
        cls.move_line_model = cls.env["account.move.line"]
        cls.currency_eur = cls.env.ref("base.EUR")
        cls.currency_usd = cls.env.ref("base.USD")
        cls.main_company = cls.env.ref("base.main_company")
        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        ).id
        cls.account_type_expenses = cls.env.ref("account.data_account_type_expenses").id

        # Update main currency = EUR
        cls.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (cls.main_company.id, cls.currency_eur.id),
        )
        # Setup Journal
        cls.journal_bank1 = cls.journal_model.search([("code", "=", "B1")], limit=1)
        if not cls.journal_bank1:
            cls.journal_bank1 = cls.journal_model.create(
                {"name": "Bank1", "type": "bank", "code": "B1"}
            )
        cls.journal_bank2 = cls.journal_model.search([("code", "=", "B2")], limit=1)
        if not cls.journal_bank2:
            cls.journal_bank2 = cls.journal_model.create(
                {"name": "Bank2", "type": "bank", "code": "B2"}
            )
        cls.journal_bank_usd_1 = cls.journal_model.search(
            [("code", "=", "USD01")], limit=1
        )
        if not cls.journal_bank_usd_1:
            cls.journal_bank_usd_1 = cls.journal_model.create(
                {
                    "name": "Bank USD 1",
                    "type": "bank",
                    "code": "USD01",
                    "currency_id": cls.currency_usd.id,
                }
            )
        cls.journal_bank_usd_2 = cls.journal_model.search(
            [("code", "=", "USD02")], limit=1
        )
        if not cls.journal_bank_usd_2:
            cls.journal_bank_usd_2 = cls.journal_model.create(
                {
                    "name": "Bank USD 2",
                    "type": "bank",
                    "code": "USD02",
                    "currency_id": cls.currency_usd.id,
                }
            )

        cls.writeoff_account_id = cls.account_model.search([("code", "=", "5001")])
        if not cls.writeoff_account_id:
            cls.writeoff_account_id = cls.account_model.create(
                {
                    "code": 5001,
                    "name": "Fee Bank Account",
                    "user_type_id": cls.account_type_expenses,
                }
            )

    def create_payment_transfer(
        self,
        journal,
        dest_journal,
        amount,
        fee=0.0,
        writeoff_account_id=False,
        writeoff_label="write-off",
        deduct_journal_id=False,
        currency=None,
    ):
        payment_dict = {
            "payment_type": "transfer",
            "journal_id": journal.id,
            "destination_journal_id": dest_journal.id,
            "amount": amount,
            "payment_date": "2020-01-20",
            "currency_id": currency or self.main_company.currency_id.id,
            "payment_method_id": self.payment_method_manual_in,
            "fee_transfer": fee or 0.0,
            "writeoff_account_id": writeoff_account_id,
            "writeoff_label": writeoff_label,
            "deduct_journal_id": deduct_journal_id,
        }
        payment_transfer = self.payment_model.create(payment_dict)
        return payment_transfer

    def test_01_payment_fee_transfer_deduct1(self):
        """ Transfer, BANK1 -> BANK2 (fee on BANK1) """
        fee = 10.0
        payment_transfer = self.create_payment_transfer(
            self.journal_bank1,
            self.journal_bank2,
            100.0,
            fee,
            self.writeoff_account_id.id,
            "Fee Transfer",
            deduct_journal_id=self.journal_bank1.id,
        )
        # Check constrain
        with self.assertRaises(ValidationError):
            payment_transfer.fee_transfer = -1
        payment_transfer.post()
        self.assertEqual(len(payment_transfer.move_line_ids), 6)
        self.assertEqual(payment_transfer.state, "posted")
        # find debit fee transfer
        move_line_fee_debit = payment_transfer.move_line_ids.filtered(
            lambda l: l.account_id == self.writeoff_account_id
        )
        self.assertEqual(move_line_fee_debit.debit, fee)
        # find credit fee transfer
        move_line_fee_credit = payment_transfer.move_line_ids.filtered(
            lambda l: l.journal_id == self.journal_bank1
            and l.account_id == self.journal_bank1.default_credit_account_id
            and l.credit == fee
        )
        self.assertEqual(move_line_fee_credit.credit, fee)

    def test_02_payment_fee_transfer_deduct2(self):
        """ Transfer, BANK1 -> BANK2 (fee on BANK2) """
        fee = 10.0
        payment_transfer = self.create_payment_transfer(
            self.journal_bank1,
            self.journal_bank2,
            100.0,
            fee,
            self.writeoff_account_id.id,
            "Fee Transfer",
            deduct_journal_id=self.journal_bank2.id,
        )
        payment_transfer.post()
        self.assertEqual(len(payment_transfer.move_line_ids), 6)
        self.assertEqual(payment_transfer.state, "posted")
        # find debit fee transfer
        move_line_fee_debit = payment_transfer.move_line_ids.filtered(
            lambda l: l.account_id == self.writeoff_account_id
        )
        self.assertEqual(move_line_fee_debit.debit, fee)
        # find credit fee transfer
        move_line_fee_credit = payment_transfer.move_line_ids.filtered(
            lambda l: l.journal_id == self.journal_bank2
            and l.account_id == self.journal_bank2.default_credit_account_id
            and l.credit == fee
        )
        self.assertEqual(move_line_fee_credit.credit, fee)

    def test_03_payment_fee_transfer_difference_bank_currency(self):
        """ Main company currency is EUR, Transfer BANK1 (EUR)-> BANK2 (USD)
            fee on BANK1"""
        balance = 100.0
        # EUR -> USD
        balance_amount_currency = self.currency_eur._convert(
            balance, self.currency_usd, self.main_company, "2020-01-20"
        )
        payment_transfer = self.create_payment_transfer(
            self.journal_bank1,
            self.journal_bank_usd_1,
            balance,
            10.0,
            self.writeoff_account_id.id,
            "Fee Transfer",
            deduct_journal_id=self.journal_bank1.id,
        )
        payment_transfer.post()
        self.assertEqual(len(payment_transfer.move_line_ids), 6)
        self.assertEqual(payment_transfer.state, "posted")

        # find bank usd debit
        move_line_bank_usd = payment_transfer.move_line_ids.filtered(
            lambda l: l.journal_id == self.journal_bank_usd_1 and l.debit
        )
        self.assertTrue(move_line_bank_usd.amount_currency > 0.0)
        self.assertEqual(move_line_bank_usd.amount_currency, balance_amount_currency)
        self.assertEqual(move_line_bank_usd.debit, balance)

    def test_04_payment_fee_transfer_difference_bank_currency(self):
        """ Main company currency is EUR, Transfer BANK1 (EUR)-> BANK2 (USD)
            fee on BANK2"""
        balance = 100.0
        fee = 10.0
        # EUR -> USD
        balance_amount_currency = self.currency_eur._convert(
            balance, self.currency_usd, self.main_company, "2020-01-20"
        )
        fee_amount_currency = self.currency_eur._convert(
            fee, self.currency_usd, self.main_company, "2020-01-20"
        )
        payment_transfer = self.create_payment_transfer(
            self.journal_bank1,
            self.journal_bank_usd_1,
            balance,
            fee,
            self.writeoff_account_id.id,
            "Fee Transfer",
            deduct_journal_id=self.journal_bank_usd_1.id,
        )
        payment_transfer.post()
        self.assertEqual(len(payment_transfer.move_line_ids), 6)
        self.assertEqual(payment_transfer.state, "posted")

        # find bank usd
        move_line_currency = payment_transfer.move_line_ids.filtered(
            lambda l: l.journal_id == self.journal_bank_usd_1 and l.amount_currency
        )
        # balance amount currency
        self.assertTrue(move_line_currency.filtered("debit").amount_currency > 0.0)
        self.assertEqual(
            move_line_currency.filtered("debit").amount_currency,
            balance_amount_currency,
        )
        self.assertEqual(move_line_currency.filtered("debit").debit, balance)
        # fee amount currency
        self.assertTrue(move_line_currency.filtered("credit").amount_currency < 0.0)
        self.assertEqual(
            move_line_currency.filtered("credit").amount_currency, -fee_amount_currency
        )
        self.assertEqual(move_line_currency.filtered("credit").credit, fee)

    def test_05_payment_fee_transfer_difference_bank_currency(self):
        """ Main company currency is EUR, Transfer BANK1 (USD)-> BANK2 (USD)
            fee on BANK1"""
        # USD
        balance_amount_currency = 100.0
        # EUR -> USD
        balance = self.currency_usd._convert(
            balance_amount_currency, self.currency_eur, self.main_company, "2020-01-20"
        )
        payment_transfer = self.create_payment_transfer(
            self.journal_bank_usd_1,
            self.journal_bank_usd_2,
            balance_amount_currency,
            10.0,
            self.writeoff_account_id.id,
            "Fee Transfer",
            deduct_journal_id=self.journal_bank_usd_1.id,
            currency=self.currency_usd.id,
        )
        payment_transfer.post()
        self.assertEqual(len(payment_transfer.move_line_ids), 6)
        self.assertEqual(payment_transfer.state, "posted")

        # find bank usd debit
        move_line_fee_bank_usd = payment_transfer.move_line_ids.filtered(
            lambda l: l.journal_id == self.journal_bank_usd_1
            and l.debit
            and l.name != "Fee Transfer"
        )
        self.assertTrue(move_line_fee_bank_usd.amount_currency > 0.0)
        self.assertEqual(
            move_line_fee_bank_usd.amount_currency, balance_amount_currency
        )
        self.assertEqual(move_line_fee_bank_usd.debit, balance)

    def test_06_payment_transfer_no_fee(self):
        """ Transfer, BANK1 -> BANK2 (no fee) """
        payment_transfer = self.create_payment_transfer(
            self.journal_bank1, self.journal_bank2, 100.0
        )
        payment_transfer.post()
        self.assertEqual(payment_transfer.state, "posted")
        self.assertEqual(len(payment_transfer.move_line_ids), 4)
