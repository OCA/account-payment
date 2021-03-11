# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    valid_discount_date = fields.Date(string="Valid Discount Date")

    def action_post(self):
        res = super().action_post()
        for rec in self:
            if rec.invoice_payment_term_id and rec.invoice_date:
                # Check payment date discount validation
                invoice_date = fields.Date.from_string(rec.invoice_date)
                # Get discount validity days from payment terms
                for line in rec.invoice_payment_term_id.line_ids:
                    rec.valid_discount_date = invoice_date + relativedelta(
                        days=line.discount_days
                    )
        return res
