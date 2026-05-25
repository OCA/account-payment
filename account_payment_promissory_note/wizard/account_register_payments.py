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
            active_ids = self.env.context.get("active_ids")
            active_model = self.env.context.get("active_model")
            if (
                active_model not in ("account.move.line", "account.move")
                or not active_ids
            ):
                return result
            records = self.env[active_model].browse(active_ids)
            moves = (
                records.mapped("move_id")
                if active_model == "account.move.line"
                else records
            )
            same_partner = len(moves.partner_id) == 1
            if records and self.group_payment and same_partner:
                self.date_due = max(moves.mapped("invoice_date_due"))
        return result
