# Copyright 2018-2021 ForgeFlow S.L.
# Copyright 2024 OERP Canada <https://www.oerp.ca>

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def js_assign_outstanding_line(self, line_id):
        self.ensure_one()
        if "paid_amount" in self.env.context:
            return super(
                AccountMove,
                self.with_context(
                    move_id=self.id,
                    line_id=line_id,
                ),
            ).js_assign_outstanding_line(line_id)
        return super().js_assign_outstanding_line(line_id)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _prepare_reconciliation_single_partial(
        self, debit_values, credit_values, shadowed_aml_values=None
    ):
        # update paid amount from front end
        if self.env.context.get("paid_amount", 0.0):
            total_paid = self.env.context.get("paid_amount", 0.0)
            credit_values["amount_residual"] = credit_values[
                "amount_residual_currency"
            ] = total_paid
        return super()._prepare_reconciliation_single_partial(
            debit_values, credit_values, shadowed_aml_values=shadowed_aml_values
        )
