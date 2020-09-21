# Copyright 2018 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2018 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountRegisterPayments(models.TransientModel):
    _name = 'account.register.payments'
    _inherit = ['account.register.payments', 'account.abstract.payment']

    def get_payment_vals(self):
        vals = super(AccountRegisterPayments, self).get_payment_vals()
        vals.update({
            'promissory_note': self.promissory_note,
            'date_due': self.date_due,
        })
        return vals

    def create_payment(self):
        # Overwrite original method for obtain payment and return action
        payment = self.env['account.payment'].create(self.get_payment_vals())
        payment.post()
        if payment.payment_method_id != self.env.ref(
                'account_check_printing.account_payment_method_check'):
            return {'type': 'ir.actions.act_window_close'}
        action = self.env.ref(
            'account.action_account_payments_payable').read()[0]
        action['views'] = [
            (self.env.ref('account.view_account_payment_form').id, 'form')]
        action['res_id'] = payment.id
        return action

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
