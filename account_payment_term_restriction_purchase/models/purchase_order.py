# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.constrains("payment_term_id")
    def _check_payment_term_id(self):
        purchase_applicable_on = self.env[
            "account.payment.term"
        ].get_purchase_applicable_on()
        for purchase in self:
            purchase_pt = purchase.payment_term_id
            purchase_pt.check_not_applicable(purchase_applicable_on, record=purchase)
