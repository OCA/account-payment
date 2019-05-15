# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def update_amount_reconcile(
            self, amount_reconcile, amount_reconcile_currency,
            sm_credit_move, sm_debit_move):
        super(AccountMoveLine, self).update_amount_reconcile(
            amount_reconcile, amount_reconcile_currency,
            sm_credit_move, sm_debit_move)
        # Check for the currency and amount_currency we can set
        amount_reconcile_currency = 0
        paid_amt = self.env.context.get('paid_amount', False)
        if paid_amt < 0:
            raise UserError(_(
                "The specified amount has to be strictly positive"))
        if sm_debit_move.currency_id == sm_credit_move.currency_id \
                and sm_debit_move.currency_id.id:
            if paid_amt:
                amount_reconcile_currency = min(
                    sm_debit_move.amount_residual_currency, paid_amt)
                paid_amt = paid_amt * sm_credit_move.company_currency_id.rate
            else:
                amount_reconcile_currency = min(
                    sm_debit_move.amount_residual_currency,
                    -sm_credit_move.amount_residual_currency)
        if paid_amt:
            amount_reconcile = min(sm_debit_move.amount_residual, paid_amt)
        else:
            amount_reconcile = min(sm_debit_move.amount_residual,
                                   -sm_credit_move.amount_residual)

        return amount_reconcile, amount_reconcile_currency
