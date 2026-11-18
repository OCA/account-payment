# Copyright 2018-2021 ForgeFlow S.L.
# Copyright 2024 OERP Canada <https://www.oerp.ca>

from odoo import api, models
from odoo.tools import float_compare


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
    def _prepare_reconciliation_amls(self, values_list, shadowed_aml_values=None):
        am_model = self.env["account.move"]
        aml_model = self.env["account.move.line"]
        partials = super()._prepare_reconciliation_amls(
            values_list=values_list, shadowed_aml_values=shadowed_aml_values
        )
        if self.env.context.get("paid_amount", 0.0):
            total_paid = self.env.context.get("paid_amount", 0.0)
            current_am = am_model.browse(self.env.context.get("move_id"))
            current_aml = aml_model.browse(self.env.context.get("line_id"))
            decimal_places = current_am.company_id.currency_id.decimal_places
            if current_am.currency_id.id != current_am.company_currency_id.id:
                total_paid = current_am.currency_id._convert(
                    total_paid,
                    current_aml.currency_id,
                    current_am.company_id,
                    current_aml.date,
                )
            for partial in partials[0]:
                partial_values = partial.get("partial_values")
                debit_line = self.browse(partial_values.get("debit_move_id"))
                credit_line = self.browse(partial_values.get("credit_move_id"))
                different_currency = (
                    debit_line.currency_id.id != credit_line.currency_id.id
                )
                to_apply = (
                    min(total_paid, partial_values.get("amount", 0.0))
                    if partial_values
                    else 0.0
                )
                partial_values.update(
                    {
                        "amount": to_apply,
                    }
                )
                if different_currency:
                    credit_currency = credit_line.company_currency_id
                    debit_currency = debit_line.company_currency_id
                    partial_values.update(
                        {
                            "debit_amount_currency": credit_currency._convert(
                                to_apply,
                                debit_line.currency_id,
                                credit_line.company_id,
                                credit_line.date,
                            ),
                            "credit_amount_currency": debit_currency._convert(
                                to_apply,
                                credit_line.currency_id,
                                debit_line.company_id,
                                debit_line.date,
                            ),
                        }
                    )
                else:
                    partial_values.update(
                        {
                            "debit_amount_currency": to_apply,
                            "credit_amount_currency": to_apply,
                        }
                    )
                total_paid -= to_apply
                if float_compare(total_paid, 0.0, precision_digits=decimal_places) <= 0:
                    break
        return partials
