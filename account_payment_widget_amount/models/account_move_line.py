# Copyright 2018-2021 ForgeFlow S.L.

from odoo import models
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
        return super(AccountMove, self).js_assign_outstanding_line(line_id)


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _prepare_reconciliation_partials(self):
        am_model = self.env["account.move"]
        aml_model = self.env["account.move.line"]
        partials = super(AccountMoveLine, self)._prepare_reconciliation_partials()
        if self.env.context.get("paid_amount", 0.0):
            total_paid_invoice_curr = self.env.context.get("paid_amount", 0.0)
            current_am = am_model.browse(self.env.context.get("move_id"))
            current_aml = aml_model.browse(self.env.context.get("line_id"))
            decimal_places = current_am.company_id.currency_id.decimal_places
            new_partials = []
            for partial in partials:
                if current_am.currency_id.id != current_am.company_currency_id.id:
                    total_paid_payment_cur = current_am.currency_id._convert(
                        total_paid_invoice_curr,
                        current_aml.currency_id,
                        current_am.company_id,
                        current_aml.date,
                    )
                debit_line = self.browse(partial.get("debit_move_id"))
                credit_line = self.browse(partial.get("credit_move_id"))
                debit_amount_currency = partial.get("debit_amount_currency", 0.0)
                credit_amount_currency = partial.get("credit_amount_currency", 0.0)
                current_aml_is_debit_line = bool(debit_line == current_aml)

                different_currency = (
                    debit_line.currency_id.id != credit_line.currency_id.id
                )
                partial_amount = partial.get("amount", 0.0)
                # When Payment currency is different with Invoice currency
                if different_currency:
                    if current_aml_is_debit_line:
                        paid_in_credit_amount_currency = (
                            debit_line.currency_id._convert(
                                total_paid_payment_cur,
                                credit_line.currency_id,
                                debit_line.company_id,
                                debit_line.date,
                            )
                        )
                        if credit_amount_currency > paid_in_credit_amount_currency:
                            to_apply = paid_in_credit_amount_currency
                            to_apply_company_curr = debit_line.currency_id._convert(
                                to_apply,
                                debit_line.company_currency_id,
                                debit_line.company_id,
                                debit_line.date,
                            )
                        else:
                            to_apply = credit_amount_currency
                            to_apply_company_curr = partial_amount
                    else:
                        paid_in_dedit_amount_currency = (
                            credit_line.currency_id._convert(
                                total_paid_payment_cur,
                                debit_line.currency_id,
                                credit_line.company_id,
                                credit_line.date,
                            )
                        )
                        if debit_amount_currency > paid_in_dedit_amount_currency:
                            to_apply = paid_in_dedit_amount_currency
                            to_apply_company_curr = debit_line.currency_id._convert(
                                to_apply,
                                debit_line.company_currency_id,
                                debit_line.company_id,
                                debit_line.date,
                            )
                        else:
                            to_apply = debit_amount_currency
                            to_apply_company_curr = partial_amount
                    partial.update(
                        {
                            "amount": to_apply_company_curr,
                            "debit_amount_currency": to_apply,
                            "credit_amount_currency": to_apply,
                        }
                    )
                # When Payment currency is the same with Invoice currency
                else:
                    if current_aml_is_debit_line:
                        to_apply = min(credit_amount_currency, total_paid_payment_cur)
                        to_apply_company_curr = credit_line.currency_id._convert(
                            to_apply,
                            debit_line.company_currency_id,
                            credit_line.company_id,
                            credit_line.date,
                        )
                    else:
                        to_apply = min(debit_amount_currency, total_paid_payment_cur)
                        to_apply_company_curr = debit_line.currency_id._convert(
                            to_apply,
                            credit_line.company_currency_id,
                            debit_line.company_id,
                            debit_line.date,
                        )
                    partial.update(
                        {
                            "amount": min(to_apply_company_curr, partial_amount),
                            "debit_amount_currency": to_apply,
                            "credit_amount_currency": to_apply,
                        }
                    )
                total_paid_invoice_curr -= to_apply
                new_partials.append(partial)
                if (
                    float_compare(
                        total_paid_invoice_curr, 0.0, precision_digits=decimal_places
                    )
                    <= 0
                ):
                    break
            return new_partials
        return partials
