# Copyright (C) 2021 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.gift_card.tests.common import TestGiftCardCommon


class TestGiftCardAccountReturn(TestGiftCardCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.so2.action_confirm()
        for line in cls.so2.order_line:
            line.write({"qty_delivered": line.product_uom_qty})
        cls.invoice = cls.so2._create_invoices()
        cls.invoice.action_post()

        cls.gift_card_tmpl = cls.env.ref(
            "account_gift_card_invoice_refund.gift_card_as_refund"
        )

        cls.move_reversal = (
            cls.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=cls.invoice.ids)
            .create(
                {
                    "refund_method": "giftcard",
                    "gift_card_tmpl_id": cls.gift_card_tmpl.id,
                }
            )
        )

        cls.move_reversal.reverse_moves()

    def test_1_create_gift_card_refund(self):
        self.assertEqual(self.invoice.payment_state, "reversed")
        # reverse Invoice
        reverse_invoice = self.env["account.move"].search(
            [("reversed_entry_id", "=", self.invoice.id)]
        )
        self.assertEqual(len(reverse_invoice), 1)
        self.assertEqual(reverse_invoice.payment_state, "paid")

    def test_2_create_gift_card_as_refund(self):
        gift_card_return = self.invoice.gift_card_return_id
        self.assertEqual(len(gift_card_return), 1)

        self.assertEqual(gift_card_return.initial_amount, self.invoice.amount_total)
        self.assertEqual(gift_card_return.gift_card_tmpl_id, self.gift_card_tmpl)
