# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time
from datetime import datetime
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, models
from odoo.tools import float_is_zero


class ReportCheckPrint(models.AbstractModel):
    _name = 'report.account_check_report.check_report'

    def _format_date_to_partner_lang(self, str_date, partner_id):
        lang_code = self.env['res.partner'].browse(partner_id).lang
        lang = self.env['res.lang']._lang_get(lang_code)
        date = datetime.strptime(str_date, DEFAULT_SERVER_DATE_FORMAT).date()
        return date.strftime(lang.date_format)

    def _get_paid_lines(self, payment):
        rec_lines = payment.move_line_ids.filtered(
            lambda l: l.account_id.reconcile)
        amls = rec_lines.matched_credit_ids.mapped('credit_move_id') + \
            rec_lines.matched_debit_ids.mapped('debit_move_id')
        amls -= rec_lines
        return amls

    def _get_residual_amount(self, payment, line):
        amt = line.amount_residual
        if amt < 0.0:
            amt *= -1
        amt = payment.company_id.currency_id.with_context(
            date=payment.payment_date).compute(
            amt, payment.currency_id)
        return amt

    def _get_paid_amount(self, payment, line):
        amount = 0.0
        total_amount_to_show = 0.0
        # We pay out
        if line.matched_credit_ids:
            amount = sum([p.amount for p in line.matched_credit_ids])
        # We receive payment
        elif line.matched_debit_ids:
            amount = sum([p.amount for p in line.matched_debit_ids])

        amount_to_show = \
            payment.company_id.currency_id.with_context(
                date=payment.payment_date).compute(
                amount, payment.currency_id)
        if not float_is_zero(
                amount_to_show,
                precision_rounding=payment.currency_id.rounding):
            total_amount_to_show = amount_to_show
        return total_amount_to_show

    def _get_total_amount(self, payment, line):
        amt = line.balance
        if amt < 0.0:
            amt *= -1
        amt = payment.company_id.currency_id.with_context(
            date=payment.payment_date).compute(
            amt, payment.currency_id)
        return amt

    @api.multi
    def render_html(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'time': time,
            'total_amount': self._get_total_amount,
            'paid_lines': self._get_paid_lines,
            'residual_amount': self._get_residual_amount,
            'paid_amount': self._get_paid_amount,
            '_format_date_to_partner_lang': self._format_date_to_partner_lang,
        }
        return self.env['report'].render(
            'account_check_report.check_report', docargs)
