# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentAcquirerGiftCard(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[("gift_card", "Gift Card")],
        ondelete={"gift_card": "set default"},
    )


class PaymentTransactionGiftCard(models.Model):
    _inherit = "payment.transaction"

    gift_card_line_id = fields.Many2one(
        "gift.card.line",
        string="Gift Card Uses",
        readonly=True,
    )

    def _add_gift_card_transaction(self, amount, card=None, code=None, line=None):
        # create the gift card line and check the card validity
        if not line:
            card = self._get_and_check_gift_card(card, code)
            line = self._create_gift_card_line(amount, card, code)

        gift_card_acquirer = self.env.ref(
            "account_payment_gift_card.payment_acquirer_gift_card"
        )

        gift_card_tx = self.create(
            {
                "currency_id": self.currency_id.id,
                "acquirer_id": gift_card_acquirer.id,
                "partner_id": self.partner_id.id,
                "amount": line.amount_used,
                "sale_order_ids": self.sale_order_ids,
            }
        )
        gift_card_tx.gift_card_line_id = line
        gift_card_tx._create_payment()

        return gift_card_tx

    def _create_gift_card_line(self, amount, card, code):
        line = self.env["gift.card.line"].create(
            {
                "gift_card_id": card.id,
                "name": card.name,
                "beneficiary_id": self.partner_id.id,
                "code": code,
                "amount_used": amount,
                "transaction_id": self.id,
                "payment_id": self.payment_id.id,
            }
        )
        return line

    def _get_and_check_gift_card(self, card=None, code=None):
        if code:
            card = self.env["gift.card"].check_gift_card_code(code)
        return card
