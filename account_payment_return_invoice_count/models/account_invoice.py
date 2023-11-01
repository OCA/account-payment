# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    returned_payment_count = fields.Integer(
        string="Payment Returned Count",
        help="Number of payments that has been later returned "
             "on which the invoice has been included.",
        default=0,
    )

    @api.multi
    def _payment_returned(self, return_line):
        super()._payment_returned(return_line)
        for rec in self:
            rec.returned_payment_count += 1
