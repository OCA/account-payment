# Copyright 2018 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2018 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountRegisterPayments(models.TransientModel):
    _name = "account.payment.register"
    _inherit = ["account.payment.register", "account.promissory.note.mixin"]

    def _create_payments(self):
        payments = super()._create_payments()
        for payment in payments:
            if not self.date_due:
                invoices = payment.reconciled_invoice_ids
                if invoices:
                    max_date = max(invoices.mapped("invoice_date_due"))
                    payment.promissory_note = self.promissory_note
                    payment.date_due = max_date
            else:
                payment.promissory_note = self.promissory_note
                payment.date_due = self.date_due
        return payments

    @api.onchange("promissory_note")
    def _onchange_promissory_note(self):
        result = super()._onchange_promissory_note()
        if not self.date_due and self.promissory_note:
            same_partner = len(self.line_ids.move_id.partner_id) == 1
            if self.line_ids and self.group_payment and same_partner:
                self.date_due = max(self.line_ids.move_id.mapped("invoice_date_due"))
        return result
