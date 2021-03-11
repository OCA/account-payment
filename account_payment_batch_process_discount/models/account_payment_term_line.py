# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import fields, models


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    def write(self, vals):
        res = super().write(vals)
        if vals.get("discount_days"):
            for item in self:
                # get all invoice related to this payment term and update
                # validity discount date
                invoice_ids = self.env["account.move"].search(
                    [
                        ("state", "=", "posted"),
                        ("payment_term_id", "=", item.payment_id.id),
                    ]
                )
                for inv in invoice_ids:
                    # Check payment date discount validation
                    invoice_date = fields.Date.from_string(inv.date_invoice)
                    # Update discount validity days
                    for line in inv.invoice_payment_term_id.line_ids:
                        inv.valid_discount_date = invoice_date + relativedelta(
                            days=line.discount_days
                        )
        return res
