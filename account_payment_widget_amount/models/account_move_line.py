# Copyright 2018 Eficent Business and IT Consulting Services S.L.

from odoo import api, fields, models, _
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
        paid_amt = self.env.context.get('paid_amount', 0.0)
        if not paid_amt:
            return temp_amount_residual, temp_amount_residual_currency, \
                amount_reconcile
        paid_amt = float(paid_amt)
        if paid_amt < 0:
            raise UserError(_(
                "The specified amount has to be strictly positive"))

        # We need those temporary value otherwise the computation might
        # be wrong below

        # Compute paid_amount currency
        if debit_move.amount_residual_currency or \
                credit_move.amount_residual_currency:

            temp_amount_residual_currency = min(
                debit_move.amount_residual_currency,
                -credit_move.amount_residual_currency,
                paid_amt)
        else:
            temp_amount_residual_currency = 0.0

        # If previous value is not 0 we compute paid amount in the company
        # currency taking into account the rate
        if temp_amount_residual_currency:
            paid_amt = debit_move.currency_id._convert(
                paid_amt, debit_move.company_id.currency_id,
                debit_move.company_id,
                credit_move.date or fields.Date.today())
        temp_amount_residual = min(debit_move.amount_residual,
                                   -credit_move.amount_residual,
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
