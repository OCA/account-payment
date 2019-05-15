from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def update_amount_reconcile(
            self, temp_amount_residual, temp_amount_residual_currency,
            amount_reconcile, credit_move, debit_move):
        return temp_amount_residual, temp_amount_residual_currency, \
            amount_reconcile

    @api.model
    def _check_remove_debit_move(self, amount_reconcile, debit_move, field):
        return amount_reconcile == debit_move[field]

    @api.model
    def _check_remove_credit_move(self, amount_reconcile, credit_move, field):
        return amount_reconcile == -credit_move[field]
