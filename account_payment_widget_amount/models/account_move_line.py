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

        # Check if amount is positive
        paid_amt = self.env.context.get('paid_amount', False)
        if paid_amt < 0:
            raise UserError(_(
                "The specified amount has to be strictly positive"))

        # We need those temporary value otherwise the computation might
        # be wrong below

        # Compute paid_amount currency
        paid_amt_currency = paid_amt and min(
            float(paid_amt), -credit_move.amount_residual_currency) or \
            -credit_move.amount_residual_currency

        temp_amount_residual_currency = min(
            debit_move.amount_residual_currency, paid_amt_currency)

        # If previous value is not 0 we compute paid amount in the company
        # currency taking into account the rate
        if temp_amount_residual_currency:
            paid_amt = paid_amt * credit_move.company_currency_id.rate
        paid_amt = paid_amt and min(
            float(paid_amt), -credit_move.amount_residual_currency) or \
            -credit_move.amount_residual

        temp_amount_residual = min(debit_move.amount_residual,
                                   paid_amt)

        amount_reconcile = temp_amount_residual_currency or \
            temp_amount_residual

        return temp_amount_residual, temp_amount_residual_currency, \
            amount_reconcile

    @api.model
    def _check_remove_debit_move(self, amount_reconcile, debit_move, field):
        res = super(AccountMoveLine, self)._check_remove_debit_move(
            amount_reconcile, debit_move, field)
        if not isinstance(self.env.context.get('paid_amount', False), bool):
            return True
        return res

    @api.model
    def _check_remove_credit_move(self, amount_reconcile, credit_move, field):
        res = super(AccountMoveLine, self)._check_remove_credit_move(
            amount_reconcile, credit_move, field)
        if not isinstance(self.env.context.get('paid_amount', False), bool):
            return True
        return res
