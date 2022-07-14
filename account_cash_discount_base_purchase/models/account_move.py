# Copyright 2022 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        """
        Inherit to also apply onchange related to partner (payment term etc)
        """
        previous_purchase = bool(self.purchase_vendor_bill_id)
        res = super()._onchange_purchase_auto_complete()
        if previous_purchase:
            self._onchange_payment_term_discount_options()
        return res
