# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains("property_supplier_payment_term_id")
    def _check_property_supplier_payment_term_id(self):
        purchase_applicable_on = self.env[
            "account.payment.term"
        ].get_purchase_applicable_on()
        for partner in self:
            partner_pt = partner.property_supplier_payment_term_id
            partner_pt.check_not_applicable(purchase_applicable_on, record=partner)
