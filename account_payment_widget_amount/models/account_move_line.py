# Copyright 2018-2021 ForgeFlow S.L.
# Copyright 2025 Aritz Olea <aritz.olea@factorlibre.com>

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
        return super(AccountMove, self).js_assign_outstanding_line(line_id)


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    @api.model
    def _prepare_reconciliation_partials(self, vals_list):
        am_model = self.env["account.move"]
        aml_model = self.env["account.move.line"]
        if self.env.context.get("paid_amount", 0.0):
            total_paid = self.env.context.get("paid_amount", 0.0)
            current_am = am_model.browse(self.env.context.get("move_id"))
            current_aml = aml_model.browse(self.env.context.get("line_id"))
            for vals in vals_list:
                aml = vals["record"]
                if aml == current_aml:
                    total_paid = current_am.currency_id._convert(
                        total_paid,
                        current_aml.currency_id,
                        current_am.company_id,
                        current_aml.move_id.date,
                    )
                    if aml.currency_id == vals["company"].currency_id:
                        sign = 1 if vals["balance"] >= 0 else -1
                        if (
                            abs(vals["amount_residual"]) < total_paid
                            or abs(vals["balance"]) < total_paid
                        ):
                            continue
                        residual_prop = abs(total_paid / vals["amount_residual"])
                        amount_prop = abs(total_paid / vals["balance"])
                        vals["amount_residual"] = total_paid * sign
                        vals["balance"] = total_paid * sign
                        vals["amount_residual_currency"] = (
                            vals["amount_residual_currency"] * residual_prop
                        )
                        vals["amount_currency"] = vals["amount_currency"] * amount_prop
                    else:
                        sign = 1 if vals["amount_currency"] >= 0 else -1
                        if (
                            abs(vals["amount_residual_currency"]) < total_paid
                            or abs(vals["amount_currency"]) < total_paid
                        ):
                            continue
                        residual_prop = abs(
                            total_paid / vals["amount_residual_currency"]
                        )
                        amount_prop = abs(total_paid / vals["amount_currency"])
                        vals["amount_residual_currency"] = total_paid * sign
                        vals["amount_currency"] = total_paid * sign
                        vals["amount_residual"] = (
                            vals["amount_residual"] * residual_prop
                        )
                        vals["balance"] = vals["balance"] * amount_prop
        return super(AccountMoveLine, self)._prepare_reconciliation_partials(
            vals_list=vals_list
        )
