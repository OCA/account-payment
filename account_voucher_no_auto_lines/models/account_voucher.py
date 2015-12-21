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
        res = super(AccountVoucher, self).onchange_partner_id(
            partner_id, journal_id, amount, currency_id, ttype, date)

        # Check that the method was called from the account payment view
        if (
            context.get('allow_auto_lines') or
            context.get('active_model') == 'account.invoice'
        ):
            return res

        if 'value' in res and 'line_cr_ids' in res['value']:
            for line in res['value']['line_cr_ids']:
                line['amount'] = 0.0
                line['reconcile'] = False

        if 'value' in res and 'line_dr_ids' in res['value']:
            for line in res['value']['line_dr_ids']:
                line['amount'] = 0.0
                line['reconcile'] = False

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

        # Check that the method was called from the account payment view
        if context.get('allow_auto_lines'):
            return res

        self.update_auto_lines(res, line_dr_ids, line_cr_ids)

        return res

    @api.multi
    def onchange_amount(
        self, amount, rate, partner_id, journal_id, currency_id,
        ttype, date, payment_rate_currency_id, company_id
    ):

        res = super(AccountVoucher, self).onchange_amount(
            amount, rate, partner_id, journal_id, currency_id,
            ttype, date, payment_rate_currency_id, company_id)

        # Check that the method was called from the account payment view
        if self.env.context.get('allow_auto_lines'):
            return res

        if res.get('value'):
            if res['value'].get('line_cr_ids'):
                del res['value']['line_cr_ids']
            if res['value'].get('line_dr_ids'):
                del res['value']['line_dr_ids']

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

                    if old_dr_line['reconcile']:
                        line['amount'] = line['amount_unreconciled']
                    else:
                        line['amount'] = old_dr_line['amount']

                else:
                    line['amount'] = 0.0
                    line['reconcile'] = False

        if 'value' in onchange_res and 'line_cr_ids' in onchange_res['value']:
            for line in onchange_res['value']['line_cr_ids']:

                if not isinstance(line, dict):
                    continue

                move_line_id = line.get('move_line_id')

                if move_line_id and move_line_id in line_cr_ids:
                    old_cr_line = line_cr_ids[move_line_id]

                    if old_cr_line['reconcile']:
                        line['amount'] = line['amount_unreconciled']
                    else:
                        line['amount'] = old_cr_line['amount']

                else:
                    line['amount'] = 0.0
                    line['reconcile'] = False

    @api.model
    def copy_auto_lines(self):
        context = self.env.context

        line_dr_ids = {
            line[2]['move_line_id']: {
                'amount': line[2]['amount'],
                'reconcile': line[2]['reconcile']
            }
            for line in context.get('line_dr_ids', [])
        }

        line_cr_ids = {
            line[2]['move_line_id']: {
                'amount': line[2]['amount'],
                'reconcile': line[2]['reconcile']
            }
            for line in context.get('line_cr_ids', [])
        }

        return line_dr_ids, line_cr_ids
