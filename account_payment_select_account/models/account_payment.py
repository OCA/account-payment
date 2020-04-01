# Copyright (C) 2016-Today: La Louve (<http://www.cooplalouve.fr/>)
# Copyright (C) 2019-Today: Druidoo (<https://www.druidoo.io>)
# @author: La Louve
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_account_id = fields.Many2one('account.account', string="Account")
    require_payment_account = fields.Boolean(
        compute="compute_require_payment_account",
        string="Require Payment Account")

    def _get_liquidity_move_line_vals(self, amount):
        '''
        @Overide the function to update the account used for the payment
        '''
        res = super(AccountPayment, self)._get_liquidity_move_line_vals(
            amount=amount)
        if self.payment_account_id:
            res['account_id'] = self.payment_account_id.id
        return res

    @api.multi
    @api.depends('journal_id',
                 'journal_id.default_debit_account_id',
                 'journal_id.default_credit_account_id')
    def compute_require_payment_account(self):
        '''
        @Function to identify if the payment requires to input the Account
        or not
        Required if
            Case 1:
                Type = Outbound (Send Money) / Transfer (Internal Transfer)
                Default Debit Account is not set
            Case 2:
                Other Payment Type
                Default Credit Account is not set
        '''
        for account_payment in self:
            if not account_payment.journal_id:
                account_payment.require_payment_account = False
                continue

            require_payment_account = False
            if account_payment.payment_type in ['outbound', 'transfer']:
                if not account_payment.journal_id.default_debit_account_id:
                    require_payment_account = True
            else:
                if not account_payment.journal_id.default_credit_account_id:
                    require_payment_account = True

            account_payment.require_payment_account = require_payment_account
