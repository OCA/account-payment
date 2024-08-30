# Copyright 2023 ForgeFlow S.L. <contact@forgeflow.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time

from odoo import api, models
from odoo.tools import float_is_zero


class ReportCheckPrint(models.AbstractModel):
    _name = "report.account_check_report.check_report"
    _description = "Report Check Print"

    def _format_date_to_partner_lang(self, date, partner_id):
        lang_code = self.env["res.partner"].browse(partner_id).lang
        lang = self.env["res.lang"]._lang_get(lang_code)
        return date.strftime(lang.date_format)

    def _get_paid_lines(self, payment):
        rec_lines = payment.line_ids.filtered(
            lambda x: x.account_id.reconcile
            and x.account_id == payment.destination_account_id
            and x.partner_id == payment.partner_id
        )
        amls = rec_lines.mapped("matched_credit_ids.credit_move_id") + rec_lines.mapped(
            "matched_debit_ids.debit_move_id"
        )
        # Include direct refunds:
        if payment.partner_type == "customer":
            amls += rec_lines.mapped(
                "matched_debit_ids.debit_move_id.matched_credit_ids."
                "credit_move_id.full_reconcile_id.reconciled_line_ids"
            ).filtered(
                lambda line: line.id
                not in rec_lines.mapped("matched_debit_ids.debit_move_id.id")
                and line.move_id.date <= payment.date
            )
        else:
            amls += rec_lines.mapped(
                "matched_credit_ids.credit_move_id.matched_debit_ids."
                "debit_move_id.full_reconcile_id.reconciled_line_ids"
            ).filtered(
                lambda line: line.id
                not in rec_lines.mapped("matched_credit_ids.credit_move_id.id")
                and line.move_id.date <= payment.date
            )
        amls -= rec_lines
        # Here we need to handle a nasty corner case.
        # Sometimes we match a payment with invoices and refunds. Internally
        # Odoo will match some invoices with their refunds, and not with the
        # payment, so the payment move line is not linked with those matches
        # invoices and refunds. But the end user was not really aware of this
        # as he probably just selected a bunch of invoices and refunds and made
        # a payment, assuming that the payment will correctly reflect the
        # refunds. In order to solve that, we will just include all the move
        # lines associated to the invoices that the user intended to pay,
        # including refunds.
        if payment.partner_type == "customer":
            invoice_amls = payment.reconciled_invoice_ids.line_ids.filtered(
                lambda x: x.account_id.reconcile
                and x.account_id == payment.destination_account_id
                and x.partner_id == payment.partner_id
            )
        else:
            invoice_amls = payment.reconciled_bill_ids.line_ids.filtered(
                lambda x: x.account_id.reconcile
                and x.account_id == payment.destination_account_id
                and x.partner_id == payment.partner_id
            )
        amls |= invoice_amls
        res = []
        invoices_checked = []
        # Another nasty corner case:
        # avoid printing more than one line for invoice where the
        # payable/receivable line is split. That happens when using
        # payment terms with several lines
        # I group the lines by invoice below
        for aml in amls:
            invoice = aml.move_id
            if invoice in invoices_checked:
                # prevent duplicated lines
                continue
            if invoice:
                invoices_checked.append(invoice)
                amls_inv = amls.filtered(lambda line: line.move_id == invoice)
                res.append([line for line in amls_inv])
            else:
                res.append([aml])
        return res

    def _get_residual_amount(self, payment, lines):
        amt = abs(lines[0].move_id.amount_total) - abs(
            self._get_paid_amount(payment, lines)
        )
        if amt < 0.0:
            amt *= -1
        amt = payment.company_id.currency_id.with_context(date=payment.date).compute(
            amt, payment.currency_id
        )
        return amt

    def _get_paid_amount_this_payment(self, payment, lines):
        "Get the paid amount for the payment at payment date"
        agg_amt = 0
        for line in lines:
            amount = 0.0
            total_paid_at_date = 0.0
            payment.mapped("reconciled_invoice_ids")
            # Considering the dates of the partial reconcile
            if line.matched_credit_ids:
                amount = -1 * sum(
                    p.amount
                    for p in line.matched_credit_ids.filtered(
                        lambda line: line.credit_move_id.date <= payment.date
                        and (
                            line.credit_move_id.payment_id == payment
                            or not line.credit_move_id.payment_id
                        )
                    )
                )
            # We receive payment
            elif line.matched_debit_ids:
                amount = sum(
                    p.amount
                    for p in line.matched_debit_ids.filtered(
                        lambda line: line.debit_move_id.date <= payment.date
                        and (
                            line.debit_move_id.payment_id == payment
                            or not line.debit_move_id.payment_id
                        )
                    )
                )

            # In case of customer payment, we reverse the amounts
            if payment.partner_type == "customer":
                amount *= -1
            amount_to_show = payment.company_id.currency_id.with_context(
                date=payment.date
            ).compute(amount, payment.currency_id)
            if not float_is_zero(
                amount_to_show, precision_rounding=payment.currency_id.rounding
            ):
                total_paid_at_date = amount_to_show
            agg_amt += total_paid_at_date
        return agg_amt

    def _get_paid_amount(self, payment, lines):
        "Get the total paid amount for all payments at the payment date"
        agg_amt = 0.0
        for line in lines:
            amount = 0.0
            total_amount_to_show = 0.0
            # Considering the dates of the partial reconcile
            if line.matched_credit_ids:
                amount = -1 * sum(
                    p.amount
                    for p in line.matched_credit_ids.filtered(
                        lambda line: line.credit_move_id.date <= payment.date
                    )
                )
            # We receive payment
            elif line.matched_debit_ids:
                amount = sum(
                    p.amount
                    for p in line.matched_debit_ids.filtered(
                        lambda line: line.debit_move_id.date <= payment.date
                    )
                )

            # In case of customer payment, we reverse the amounts
            if payment.partner_type == "customer":
                amount *= -1
            amount_to_show = payment.company_id.currency_id.with_context(
                date=payment.date
            ).compute(amount, payment.currency_id)
            if not float_is_zero(
                amount_to_show, precision_rounding=payment.currency_id.rounding
            ):
                total_amount_to_show = amount_to_show
            agg_amt += total_amount_to_show
        return agg_amt

    def _get_total_amount(self, payment, lines):
        agg_amt = 0
        for line in lines:
            amt = line.balance
            if amt < 0.0 or line.move_id.move_type in ("in_refund", "out_refund"):
                amt *= -1
            amt = payment.company_id.currency_id.with_context(
                date=payment.date
            ).compute(amt, payment.currency_id)
            agg_amt += amt
        return agg_amt

    @api.model
    def _get_report_values(self, docids, data=None):
        payments = self.env["account.payment"].browse(docids)
        docargs = {
            "doc_ids": docids,
            "doc_model": "account.payment",
            "docs": payments,
            "time": time,
            "total_amount": self._get_total_amount,
            "paid_lines": self._get_paid_lines,
            "residual_amount": self._get_residual_amount,
            "paid_amount": self._get_paid_amount_this_payment,
            "_format_date_to_partner_lang": self._format_date_to_partner_lang,
        }
        return docargs
