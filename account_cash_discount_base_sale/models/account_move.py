# Copyright 2022 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def create(self, vals):
        """
        Apply onchange if there was a payment_term_id on sale_order to set payment term etc
        """
        ret = super().create(vals)
        if self.env.context.get("apply_onchange_payment_term"):
            ret._onchange_payment_term_discount_options()
        return ret
