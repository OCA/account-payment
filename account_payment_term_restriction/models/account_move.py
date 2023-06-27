# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models

MOVE_TYPE_MAP = {
    "out_invoice": ["sale", "all"],
    "out_refund": ["sale", "all"],
    "in_invoice": ["purchase", "all"],
    "in_refund": ["purchase", "all"],
}


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _get_payment_term_applicable_on_type_mapping(self):
        """
        Returns a dictionary with the different account.move types, having as the value
        all the applicable on options for which the account.payment.term will not
        trigger an error. (applicable_on field on model account.payment.term).

        :return: dictionary with the account.move types and the applicable on as the value
        """
        all_applicable_on = [
            x[0] for x in self.env["account.payment.term"]._selection_applicable_on()
        ]
        return {
            **MOVE_TYPE_MAP,
            **{
                type[0]: all_applicable_on
                for type in self._fields["move_type"].selection
                if type[0] not in MOVE_TYPE_MAP.keys()
            },
        }

    @api.constrains("invoice_payment_term_id")
    def _check_invoice_payment_term_id(self):
        applicable_on_type_mapping = self._get_payment_term_applicable_on_type_mapping()
        moves = self.filtered(lambda move: move.invoice_payment_term_id)
        for move in moves:
            applicable_on = applicable_on_type_mapping.get(move.move_type)
            move_pt = move.invoice_payment_term_id
            move_pt.check_not_applicable(applicable_on, record=move)
