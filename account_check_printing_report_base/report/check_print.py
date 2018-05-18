# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# (http://www.eficent.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time
from odoo import api, exceptions, models, _
from odoo.tools import float_is_zero


class ReportCheckPrint(models.AbstractModel):
    _name = 'report.account_check_printing_report_base.report_check_base'

    def fill_stars(self, amount_in_word):
        if amount_in_word and len(amount_in_word) < 100:
            stars = 100 - len(amount_in_word)
            return ' '.join([amount_in_word, '*' * stars])
        else:
            return amount_in_word

    @api.multi
    def get_paid_lines(self, payments):
        lines = {}
        for payment in payments:
            lines[payment.id] = []
            for invoice in payment.invoice_ids:
                amount_currency = 0.0
                amount = 0.0
                date_due = invoice.date_due
                due_lines = invoice.move_id.mapped('line_ids').filtered(
                    lambda x: (
                        x.account_id.internal_type in
                        ('receivable', 'payable') and x.date_maturity
                    )
                )
                if due_lines:
                    date_due = min(due_lines.mapped('date_maturity'))
                line = {
                    'date_due': date_due,
                    'reference': invoice.reference,
                    'number': invoice.number,
                    'amount_total': invoice.amount_total,
                    'residual': invoice.residual,
                    'paid_amount': 0.0,
                }
                if invoice.type == 'out_refund':
                    line['amount_total'] *= -1
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
                line['paid_amount'] = total_amount_to_show
                lines[payment.id].append(line)
        return lines

    @api.multi
    def render_html(self, docids, data=None):
        payments = self.env['account.payment'].browse(docids)
        paid_lines = self.get_paid_lines(payments)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'time': time,
            'fill_stars': self.fill_stars,
            'paid_lines': paid_lines
        }
        if self.env.user.company_id.check_layout_id:
            return self.env['report'].render(
                self.env.user.company_id.check_layout_id.report,
                docargs)
        raise exceptions.Warning(_('You must define a check layout'))
