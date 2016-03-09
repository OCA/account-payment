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

from openerp.osv import orm

from openerp.addons.account_voucher import account_voucher as base_module


def copy_lines(context=None):

    line_dr_ids = {
        line[2]['move_line_id']: {
            'amount': line[2]['amount'],
            'type': line[2]['type'],
            'reconcile': line[2]['reconcile']
        }
        for line in context.get('line_dr_ids', [])
        if line[2] and line[2]['amount'] and
        line[2].get('type', False) == 'dr'
    }

    line_cr_ids = {
        line[2]['move_line_id']: {
            'amount': line[2]['amount'],
            'type': line[2]['type'],
            'reconcile': line[2]['reconcile']
        }
        for line in context.get('line_cr_ids', [])
        if line[2] and line[2]['amount'] and
        line[2].get('type', False) == 'cr'
    }

    return line_dr_ids, line_cr_ids


def update_lines(onchange_res, line_dr_ids, line_cr_ids):
    if 'value' in onchange_res and 'line_dr_ids' in onchange_res['value']:
        for line in onchange_res['value']['line_dr_ids']:

            move_line_id = line.get('move_line_id', False)

            if move_line_id and move_line_id in line_dr_ids:
                old_dr_line = line_dr_ids[move_line_id]

                if old_dr_line['reconcile']:
                    line['amount'] = line['amount_unreconciled']
                else:
                    line['amount'] = old_dr_line['amount']

                if line['amount_unreconciled'] == line['amount']:
                    line['reconcile'] = True
                else:
                    line['reconcile'] = False

            else:
                line['amount'] = 0.0
                line['reconcile'] = False

    if 'value' in onchange_res and 'line_cr_ids' in onchange_res['value']:
        for line in onchange_res['value']['line_cr_ids']:

            move_line_id = line.get('move_line_id', False)

            if move_line_id and move_line_id in line_cr_ids:
                old_cr_line = line_cr_ids[move_line_id]

                if old_cr_line['reconcile']:
                    line['amount'] = line['amount_unreconciled']
                else:
                    line['amount'] = old_cr_line['amount']

                if line['amount_unreconciled'] == line['amount']:
                    line['reconcile'] = True
                else:
                    line['reconcile'] = False

            else:
                line['amount'] = 0.0
                line['reconcile'] = False


class account_voucher(orm.Model):

    _inherit = 'account.voucher'

    def onchange_partner_id(self, cr, uid, ids, *args, **kwargs):

        context = kwargs.get('context', False) or args[-1]
        res = super(account_voucher, self).onchange_partner_id(
            cr, uid, ids, *args, **kwargs)

        # Check that the method was called from the account payment view
        if context.get('allow_auto_lines', False) or \
                context.get('active_model', False) == 'account.invoice':
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

    def onchange_journal(self, cr, uid, ids, *args, **kwargs):

        context = kwargs.get('context', False) or args[-1]

        line_dr_ids, line_cr_ids = copy_lines(context)

        res = super(account_voucher, self).onchange_journal(
            cr, uid, ids, *args, **kwargs)

        # Check that the method was called from the account payment view
        if context.get('allow_auto_lines', False):
            return res

        update_lines(res, line_dr_ids, line_cr_ids)

        return res


def onchange_amount(
    self, cr, uid, ids, amount, rate, partner_id, journal_id,
    currency_id, ttype, date, payment_rate_currency_id, company_id,
    context=None
):
    """
    Patch the original onchange_amount method so that it does not
    refresh the list of voucher lines when not required.
    """
    if context is None:
        context = {}

    ctx = context.copy()
    ctx.update({'date': date})
    currency_id = currency_id or self.pool.get('res.company').browse(
        cr, uid, company_id, context=ctx).currency_id.id
    voucher_rate = self.pool.get('res.currency').read(
        cr, uid, currency_id, ['rate'], context=ctx)['rate']
    ctx.update({
        'voucher_special_currency': payment_rate_currency_id,
        'voucher_special_currency_rate': rate * voucher_rate})

    if context.get('allow_auto_lines'):
        res = self.recompute_voucher_lines(
            cr, uid, ids, partner_id, journal_id, amount, currency_id,
            ttype, date, context=ctx)

    else:
        res = {'value': {}}

    vals = self.onchange_rate(
        cr, uid, ids, rate, amount, currency_id,
        payment_rate_currency_id, company_id, context=ctx)

    for key in vals.keys():
        res[key].update(vals[key])

    return res


base_module.account_voucher.onchange_amount = onchange_amount
