# Copyright 2018 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2018 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.register.payments'

    def get_payments_vals(self):
        vals = super().get_payments_vals()
        for val in vals:
            if not self.date_due:
                invoices = self.env["account.invoice"].browse(val["invoice_ids"][0][2])
                max_date = max(invoices.mapped("date_due"))
                val.update(
                    {"promissory_note": self.promissory_note, "date_due": max_date}
                )
            else:
                val.update(
                    {"promissory_note": self.promissory_note, "date_due": self.date_due}
                )
        return vals

    @api.onchange('promissory_note')
    def _onchange_promissory_note(self):
        super()._onchange_promissory_note()
        if not self.date_due and self.promissory_note:
            active_ids = self._context.get('active_ids')
            invoices = self.env['account.invoice'].browse(active_ids)
            partner = invoices[0].partner_id
            same_partner = True
            for invoice in invoices:
                if invoice.partner_id != partner:
                    same_partner = False
            if invoices and self.group_invoices and same_partner:
                self.date_due = max(invoices.mapped('date_due'))
