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

    def _get_payed_amount(self, invoice):
        amount_currency = 0.0
        amount = 0.0
        total_amount_to_show = 0.0
        for pay in invoice.payment_move_line_ids:
            payment_currency_id = False
            if invoice.type in ('out_invoice', 'in_refund'):
                amount = sum(
                    [p.amount for p in pay.matched_debit_ids if
                     p.debit_move_id in invoice.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in
                                       pay.matched_debit_ids if
                                       p.debit_move_id in
                                       invoice.move_id.line_ids])
                if pay.matched_debit_ids:
                    payment_currency_id = \
                        all(
                            [p.currency_id ==
                             pay.matched_debit_ids[0].currency_id
                             for p in pay.matched_debit_ids]) \
                        and pay.matched_debit_ids[0].currency_id \
                        or False
            elif invoice.type in ('in_invoice', 'out_refund'):
                amount = sum(
                    [p.amount for p in pay.matched_credit_ids if
                     p.credit_move_id in invoice.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in
                                       pay.matched_credit_ids if
                                       p.credit_move_id in
                                       invoice.move_id.line_ids])
                if pay.matched_credit_ids:
                    payment_currency_id = \
                        all(
                            [p.currency_id ==
                             pay.matched_credit_ids[0].currency_id
                             for p in pay.matched_credit_ids]) \
                        and pay.matched_credit_ids[0].currency_id \
                        or False

            if payment_currency_id and payment_currency_id == \
                    invoice.currency_id:
                amount_to_show = amount_currency
            else:
                amount_to_show = \
                    pay.company_id.currency_id.with_context(
                        date=pay.date).compute(
                        amount, invoice.currency_id)
            if not float_is_zero(
                    amount_to_show,
                    precision_rounding=invoice.currency_id.rounding):
                total_amount_to_show += amount_to_show
        if invoice.type in ['in_refund', 'out_refund']:
            total_amount_to_show *= -1
        return total_amount_to_show

    def _get_total_amount(self, invoice):
        factor = 1
        if invoice.type == 'out_refund':
            factor = -1
        return factor * invoice.amount_total

    @api.multi
    def render_html(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'time': time,
            'total_amount': self._get_total_amount,
            'payed_amount': self._get_payed_amount,
            '_format_date_to_partner_lang': self._format_date_to_partner_lang,
        }
        return self.env['report'].render(
            'account_check_report.check_report', docargs)
