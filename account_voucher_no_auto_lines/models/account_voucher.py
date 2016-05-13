# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import api, models


class AccountVoucher(models.Model):

    _inherit = 'account.voucher'

    @api.multi
    def onchange_partner_id(
        self, partner_id, journal_id, amount, currency_id, ttype, date
    ):
        context = self.env.context

        line_dr_ids, line_cr_ids = self.copy_auto_lines()

        res = super(AccountVoucher, self).onchange_partner_id(
            partner_id, journal_id, amount, currency_id, ttype, date)

        if (
            not self.env.user.company_id.disable_voucher_auto_lines or
            context.get('allow_auto_lines') or
            context.get('active_model') == 'account.invoice'
        ):
            return res

        self.update_auto_lines(res, line_dr_ids, line_cr_ids)

        return res

    @api.multi
    def onchange_journal(
        self, journal_id, line_ids, tax_id, partner_id,
        date, amount, ttype, company_id
    ):
        context = self.env.context

        line_dr_ids, line_cr_ids = self.copy_auto_lines()

        res = super(AccountVoucher, self).onchange_journal(
            journal_id, line_ids, tax_id, partner_id, date,
            amount, ttype, company_id)

        if (
            not self.env.user.company_id.disable_voucher_auto_lines or
            context.get('allow_auto_lines') or
            context.get('active_model') == 'account.invoice'
        ):
            return res

        self.update_auto_lines(res, line_dr_ids, line_cr_ids)

        return res

    @api.model
    def update_auto_lines(self, onchange_res, line_dr_ids, line_cr_ids):
        if not onchange_res:
            return

        if 'value' in onchange_res and 'line_dr_ids' in onchange_res['value']:
            for line in onchange_res['value']['line_dr_ids']:

                if not isinstance(line, dict):
                    continue

                move_line_id = line.get('move_line_id')

                if move_line_id and move_line_id in line_dr_ids:
                    old_dr_line = line_dr_ids[move_line_id]
                    line['amount'] = old_dr_line['amount']

                else:
                    line['amount'] = 0
                    line['reconcile'] = False

        if 'value' in onchange_res and 'line_cr_ids' in onchange_res['value']:
            for line in onchange_res['value']['line_cr_ids']:

                if not isinstance(line, dict):
                    continue

                move_line_id = line.get('move_line_id')

                if move_line_id and move_line_id in line_cr_ids:
                    old_cr_line = line_cr_ids[move_line_id]
                    line['amount'] = old_cr_line['amount']

                else:
                    line['amount'] = 0
                    line['reconcile'] = False

    @api.model
    def copy_auto_lines(self):
        line_dr_ids = {}
        line_cr_ids = {}

        old_line_cr_ids = self.env.context.get('line_cr_ids', [])
        old_line_dr_ids = self.env.context.get('line_dr_ids', [])

        for line in old_line_dr_ids:
            if len(line) != 3 or not isinstance(line[2], dict):
                continue

            line_dr_ids[line[2].get('move_line_id')] = {
                'amount': line[2].get('amount'),
                'reconcile': line[2].get('reconcile'),
            }

        for line in old_line_cr_ids:
            if len(line) != 3 or not isinstance(line[2], dict):
                continue

            line_cr_ids[line[2].get('move_line_id')] = {
                'amount': line[2].get('amount'),
                'reconcile': line[2].get('reconcile'),
            }

        return line_dr_ids, line_cr_ids

    @api.multi
    def onchange_amount(
        self, amount, rate, partner_id, journal_id,
        currency_id, ttype, date, payment_rate_currency_id, company_id
    ):
        """
        Patch the original onchange_amount method so that it does not
        refresh the list of voucher lines when not required.
        """
        self = self.with_context(date=date)

        if currency_id:
            currency = self.env['res.currency'].browse(currency_id)
        else:
            company = self.env['res.company'].browse(company_id)
            currency = company.currency_id

        voucher_rate = currency.rate

        self = self.with_context(
            voucher_special_currency=payment_rate_currency_id,
            voucher_special_currency_rate=rate * voucher_rate
        )

        if self.env.context.get('allow_auto_lines'):
            res = self.recompute_voucher_lines(
                partner_id, journal_id, amount, currency_id,
                ttype, date)
        else:
            res = {'value': {}}

        vals = self.onchange_rate(
            rate, amount, currency_id, payment_rate_currency_id, company_id)

        for key in vals.keys():
            res[key].update(vals[key])

        return res
