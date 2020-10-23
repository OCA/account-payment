# Copyright 2018 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2018 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.register.payments'

    def get_payments_vals(self):
        vals = super(AccountRegisterPayments, self).get_payments_vals()
        for val in vals:
            val.update({
                'promissory_note': self.promissory_note,
                'date_due': self.date_due,
            })
        return vals

    @api.onchange('promissory_note')
    def _onchange_promissory_note(self):
        super()._onchange_promissory_note()
        if not self.date_due and self.promissory_note:
            invoices = False
            if self._name == 'account.register.payments':
                active_ids = self._context.get('active_ids')
                invoices = self.env['account.invoice'].browse(active_ids)
            if invoices:
                self.date_due = max(invoices.mapped('date_due'))
