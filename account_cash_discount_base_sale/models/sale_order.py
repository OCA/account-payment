# Copyright 2022 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False):
        """
        Force onchange on creation of account move to set payment term etc.
        """
        if self.payment_term_id:
            # force onchange after create
            ret = super(
                SaleOrder, self.with_context(apply_onchange_payment_term=True)
            )._create_invoices(grouped, final)
        else:
            ret = super()._create_invoices(grouped, final)
        return ret
