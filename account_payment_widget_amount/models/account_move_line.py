# Copyright 2018 Eficent Business and IT Consulting Services S.L.

from odoo import api, models, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def update_amount_reconcile(
            self, temp_amount_residual, temp_amount_residual_currency,
            amount_reconcile, credit_move, debit_move):

        super(AccountMoveLine, self).update_amount_reconcile(
            temp_amount_residual, temp_amount_residual_currency,
            amount_reconcile, credit_move, debit_move)

        paid_amt = self.env.context.get('paid_amount', False)

        if paid_amt < 0:
            raise UserError(_(
                "The specified amount has to be strictly positive"))

        # We need those temporary value otherwise the computation might
        # be wrong below
        if paid_amt:
            temp_amount_residual_currency = min(
                debit_move.amount_residual_currency, paid_amt)
            if temp_amount_residual_currency:
                paid_amt = paid_amt * credit_move.company_currency_id.rate
            temp_amount_residual = min(debit_move.amount_residual,
                                       paid_amt)
        else:
            temp_amount_residual = min(debit_move.amount_residual,
                                       -credit_move.amount_residual)
            temp_amount_residual_currency = min(
                debit_move.amount_residual_currency,
                -credit_move.amount_residual_currency)

        amount_reconcile = temp_amount_residual_currency or \
            temp_amount_residual

        return temp_amount_residual, temp_amount_residual_currency, \
            amount_reconcile

    @api.model
    def _check_remove_debit_move(self, amount_reconcile, debit_move, field):
        res = super(AccountMoveLine, self)._check_remove_debit_move(
            amount_reconcile, debit_move, field)
        if self.env.context.get('paid_amount', False):
            return True
        return res

    @api.model
    def _check_remove_credit_move(self, amount_reconcile, credit_move, field):
        res = super(AccountMoveLine, self)._check_remove_credit_move(
            amount_reconcile, credit_move, field)
        if self.env.context.get('paid_amount', False):
            return True
        return res
