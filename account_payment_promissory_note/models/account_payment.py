# Copyright 2018 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2018 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ["account.payment", "account.promissory.note.mixin"]

    @api.onchange("promissory_note")
    def _onchange_promissory_note(self):
        result = super()._onchange_promissory_note()
        if not self.date_due and self.promissory_note:
            invoices = self.reconciled_invoice_ids
            same_partner = len(invoices.mapped("partner_id")) == 1
            if invoices and same_partner:
                self.date_due = max(invoices.mapped("invoice_date_due"))
        return result

    def write(self, vals):
        for payment in self:
            lines = payment.move_id.line_ids
            if "promissory_note" in vals:
                if not vals["promissory_note"]:
                    lines.date_maturity = vals.get("date", payment.date)
                elif "date_due" in vals:
                    lines.date_maturity = vals["date_due"]
            elif payment.promissory_note and "date_due" in vals:
                lines.date_maturity = vals["date_due"]
        return super().write(vals)
