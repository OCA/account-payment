# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import Form, SingleTransactionCase


class TestFeeTransfer(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal_model = cls.env["account.journal"]
        cls.payment_model = cls.env["account.payment"]
        cls.account_model = cls.env["account.account"]
        cls.move_line_model = cls.env["account.move.line"]
        cls.currency_eur_id = cls.env.ref("base.EUR")
        cls.currency_usd_id = cls.env.ref("base.USD")
        cls.main_company = cls.env.ref("base.main_company")
        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        ).id
        cls.account_type_expenses = cls.env.ref("account.data_account_type_expenses").id

        # Update main currency = EUR
        cls.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (cls.main_company.id, cls.currency_eur_id.id),
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

    def create_batch_transfer(self, payment, number, amount, fee=0.0):
        lines = []
        for num in range(number):
            lines.append(
                (
                    0,
                    0,
                    {
                        "description": "Description %s" % str(num),
                        "amount": amount,
                        "fee": fee,
                        "payment_id": payment.id,
                    },
                )
            )
        payment.batch_transfer_ids = lines
        return payment

    def test_01_payment_batch_transfer_deduct1(self):
        """ Transfer 2 transaction, BANK1 -> BANK2 (fee on BANK1) """
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
        # check fee transfer when choose use batch transfer
        self.assertEqual(payment_transfer.fee_transfer, 10.0)
        with Form(payment_transfer) as f:
            f.use_batch_transfer = True
        payment_transfer = f.save()
        self.assertEqual(payment_transfer.fee_transfer, 0.0)

        # Not have a batch transfer and create batch transfer
        with self.assertRaises(ValidationError):
            payment_transfer.post()
        payment_transfer = self.create_batch_transfer(payment_transfer, 2, 50.0, 5.0)
        self.assertEqual(len(payment_transfer.batch_transfer_ids), 2)
        self.assertEqual(
            sum(payment_transfer.batch_transfer_ids.mapped("amount")), 50.0 * 2
        )
        self.assertEqual(
            sum(payment_transfer.batch_transfer_ids.mapped("fee")), 5.0 * 2
        )
        # Check case not input Deduct From
        deduct = payment_transfer.deduct_journal_id
        payment_transfer.deduct_journal_id = False
        with self.assertRaises(ValidationError):
            payment_transfer.post()
        payment_transfer.deduct_journal_id = deduct
        # Post payment and check journal entry
        payment_transfer.post()
        self.assertEqual(payment_transfer.state, "posted")
        self.assertEqual(len(payment_transfer.move_line_ids.account_id), 4)
        self.assertEqual(len(payment_transfer.move_line_ids), 10)
        # find debit fee transfer
        move_line_fee_debit = payment_transfer.move_line_ids.filtered(
            lambda l: l.account_id == self.writeoff_account_id
        )
        self.assertEqual(len(move_line_fee_debit.mapped("debit")), 2)
        self.assertEqual(sum(move_line_fee_debit.mapped("debit")), 10.0)
        # find credit fee transfer
        move_line_fee_credit = payment_transfer.move_line_ids.filtered(
            lambda l: l.journal_id == self.journal_bank1
            and l.account_id == self.journal_bank1.default_credit_account_id
            and l.credit == fee / 2
        )
        self.assertEqual(len(move_line_fee_credit.mapped("credit")), 2)
        self.assertEqual(sum(move_line_fee_credit.mapped("credit")), 10.0)

    def test_02_payment_fee_transfer_multi_currency(self):
        """ Transfer, BANK1 -> BANK2 (fee on BANK2) and multi currency"""
        fee = 10.0
        balance = self.currency_usd_id._convert(
            fee / 2, self.currency_eur_id, self.main_company, "2020-01-20"
        )
        payment_transfer = self.create_payment_transfer(
            self.journal_bank1,
            self.journal_bank2,
            100.0,
            fee,
            self.writeoff_account_id.id,
            "Fee Transfer",
            deduct_journal_id=self.journal_bank2.id,
            currency=self.currency_usd_id.id,
        )
        with Form(payment_transfer) as f:
            f.use_batch_transfer = True
        payment_transfer = f.save()
        payment_transfer = self.create_batch_transfer(payment_transfer, 2, 50.0, 5.0)
        self.assertEqual(len(payment_transfer.batch_transfer_ids), 2)
        self.assertEqual(
            sum(payment_transfer.batch_transfer_ids.mapped("amount")), 50.0 * 2
        )
        self.assertEqual(
            sum(payment_transfer.batch_transfer_ids.mapped("fee")), 5.0 * 2
        )

        payment_transfer.post()
        self.assertEqual(payment_transfer.state, "posted")
        # find debit fee transfer
        move_line_fee_debit = payment_transfer.move_line_ids.filtered(
            lambda l: l.account_id == self.writeoff_account_id
        )
        self.assertEqual(sum(move_line_fee_debit.mapped("amount_currency")), fee)
        self.assertEqual(sum(move_line_fee_debit.mapped("debit")), balance * 2)
        # find credit fee transfer
        move_line_fee_credit = payment_transfer.move_line_ids.filtered(
            lambda l: l.journal_id == self.journal_bank2
            and l.account_id == self.journal_bank2.default_credit_account_id
            and l.amount_currency == -fee / 2
        )
        self.assertTrue(sum(move_line_fee_credit.mapped("amount_currency")) < 0.0)
        self.assertEqual(sum(move_line_fee_credit.mapped("amount_currency")), -fee)
        self.assertEqual(sum(move_line_fee_credit.mapped("credit")), balance * 2)

    def test_03_payment_transfer_no_fee(self):
        """ Transfer, BANK1 -> BANK2 (no fee) """
        payment_transfer = self.create_payment_transfer(
            self.journal_bank1, self.journal_bank2, 100.0
        )
        payment_transfer.post()
        self.assertEqual(payment_transfer.state, "posted")
        self.assertEqual(len(payment_transfer.move_line_ids), 4)
