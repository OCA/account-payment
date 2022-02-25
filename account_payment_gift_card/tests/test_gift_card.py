# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions

from odoo.addons.gift_card.tests.common import TestGiftCardCommon


class PaymentGiftCardTest(TestGiftCardCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        gift_card_acquirer = cls.env.ref(
            "account_payment_gift_card.payment_acquirer_gift_card"
        )

        cls.tx = cls.env["payment.transaction"].create(
            {
                "reference": "gift_card_test",
                "currency_id": cls.company.currency_id.id,
                "acquirer_id": gift_card_acquirer.id,
                "partner_id": cls.partner_1.id,
                "amount": 500.0,
            }
        )

    def test_1_payment_with_gift_card_code(self):
        # Find the gift card by code
        tx_gift_card = self.tx._add_gift_card_transaction(amount=20, code=self.gc1.code)

        self.assertTrue(tx_gift_card.gift_card_line_id)
        self.assertEqual(tx_gift_card.amount, 20)

        payment = tx_gift_card.payment_id
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, 20)
        self.assertRecordValues(
            payment.line_ids,
            [
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 20.0,
                    "credit": 0.0,
                },
                {
                    "journal_id": self.gift_card_journal.id,
                    "debit": 0.0,
                    "credit": 20.0,
                },
            ],
        )

    def test_2_payment_with_gift_card(self):
        # Validation of the gift card by beneficiary partner
        tx_gift_card = self.tx._add_gift_card_transaction(amount=30, card=self.gc2)

        self.assertTrue(tx_gift_card.gift_card_line_id)
        self.assertEqual(tx_gift_card.amount, 30)

        payment = tx_gift_card.payment_id
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, 30)

    def test_3_gift_card_not_validated(self):
        # Wrong code
        with self.assertRaises(exceptions.UserError) as exc:
            self.tx._add_gift_card_transaction(amount=20, code="blabla")
        self.assertEqual(
            exc.exception.name,
            ("The Gift Card Code is invalid."),
        )

        # Wrong partner
        gc3 = self.gc1.copy({"beneficiary_id": self.partner_2.id})
        with self.assertRaises(exceptions.UserError) as exc:
            self.tx._add_gift_card_transaction(amount=30, card=gc3)
        self.assertEqual(
            exc.exception.name,
            ("The Gift Card Beneficiary is invalid."),
        )
