# Copyright 2016 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
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
        rec_lines = payment.move_line_ids.filtered(
            lambda x: x.account_id.reconcile
            and x.account_id == payment.destination_account_id
            and x.partner_id == payment.partner_id
        )
        amls = rec_lines.mapped("matched_credit_ids.credit_move_id") + rec_lines.mapped(
            "matched_debit_ids.debit_move_id"
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
        invoice_amls = payment.invoice_ids.payment_move_line_ids.filtered(
            lambda x: x.account_id.reconcile
            and x.account_id == payment.destination_account_id
            and x.partner_id == payment.partner_id
        )
        amls |= invoice_amls
        return amls

    def _get_residual_amount(self, payment, line):
        amt = line.amount_residual
        if amt < 0.0:
            amt *= -1
        amt = payment.company_id.currency_id.with_context(
            date=payment.payment_date
        ).compute(amt, payment.currency_id)
        return amt

    def _get_paid_amount(self, payment, line):
        amount = 0.0
        total_amount_to_show = 0.0
        # We pay out
        if line.matched_credit_ids:
            amount = -1 * sum(p.amount for p in line.matched_credit_ids)
        # We receive payment
        elif line.matched_debit_ids:
            amount = sum(p.amount for p in line.matched_debit_ids)

        # In case of customer payment, we reverse the amounts
        if payment.partner_type == "customer":
            amount *= -1

        amount_to_show = payment.company_id.currency_id.with_context(
            date=payment.payment_date
        ).compute(amount, payment.currency_id)
        if not float_is_zero(
            amount_to_show, precision_rounding=payment.currency_id.rounding
        ):
            total_amount_to_show = amount_to_show
        return total_amount_to_show

    def _get_total_amount(self, payment, line):
        amt = line.balance
        if amt < 0.0:
            amt *= -1
        amt = payment.company_id.currency_id.with_context(
            date=payment.payment_date
        ).compute(amt, payment.currency_id)
        return amt

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
            "paid_amount": self._get_paid_amount,
            "_format_date_to_partner_lang": self._format_date_to_partner_lang,
        }
        return docargs
