# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    @api.multi
    def _payment_returned(self, return_line):
        super()._payment_returned(return_line)
        for rec in self:
            if (
                rec.invoice_id
                and self.company_id.account_payment_return_threshold != 0
                and rec.invoice_id.returned_payment_count
                >= self.company_id.account_payment_return_threshold
            ):
                rec.write({"blocked": True})
