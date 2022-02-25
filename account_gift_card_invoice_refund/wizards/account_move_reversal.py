# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    gift_card_tmpl_id = fields.Many2one(
        "gift.card.template", string="Gift Card Template"
    )

    refund_method = fields.Selection(
        selection_add=[("giftcard", "Gift Card")],
        ondelete={"giftcard": "cascade"},
    )

    def reverse_moves(self):
        self.ensure_one()
        if self.refund_method == "giftcard":
            moves = self.move_ids
            reason = self.reason or "Return By Gift Card"
            super().with_context(
                active_ids=moves.ids, active_model="account.move"
            ).create(
                {"refund_method": "cancel", "reason": reason, "date_mode": "entry"}
            ).reverse_moves()
            for move in moves:

                tmpl = self.gift_card_tmpl_id

                self.env["gift.card"].create(
                    {
                        "invoice_id": move.id,
                        "initial_amount": move.amount_total,
                        "is_divisible": tmpl.is_divisible,
                        "duration": tmpl.duration,
                        "buyer_id": move.partner_id.id,
                        "gift_card_tmpl_id": tmpl.id,
                    }
                )

                move.gift_card_return_id = self.env["gift.card"].search(
                    [("invoice_id", "=", move.id)]
                )
        else:
            super().reverse_moves()
