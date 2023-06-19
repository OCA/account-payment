# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.constrains("payment_term_id")
    def _check_payment_term_id(self):
        sale_applicable_on = self.env["account.payment.term"].get_sale_applicable_on()
        for sale in self:
            sale_pt = sale.payment_term_id
            sale_pt.check_not_applicable(sale_applicable_on, record=sale)
