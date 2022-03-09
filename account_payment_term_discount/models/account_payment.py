# Copyright 2020 Open Source Integrators (http://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        res = super().action_post()
        context = dict(self._context or {})
        if context.get("batch", False) and context.get("active_model") == "account.move":
            invoices_ids = self.env["account.move"].browse(context.get("active_ids"))
            for invoice in invoices_ids.filtered(lambda l: l.discount_amt):
                invoice.write({"discount_taken": invoice.discount_amt})
        return res
