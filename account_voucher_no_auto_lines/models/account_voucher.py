# -*- coding: utf-8 -*-
# © 2016 Joao Alfredo Gama Batista, Kitti U.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


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


class AccountVoucher(models.Model):

    _inherit = 'account.voucher'

    def onchange_partner_id(self, cr, uid, ids, *args, **kwargs):

        context = kwargs.get('context', False) or args[-1]
        res = super(AccountVoucher, self).onchange_partner_id(
            cr, uid, ids, *args, **kwargs)

        # Check that the method was called from the account payment view
        if (isinstance(context, dict) and
            (context.get('allow_auto_lines', False) or
             context.get('active_model', False) == 'account.invoice')):
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

        res = super(AccountVoucher, self).onchange_journal(
            cr, uid, ids, *args, **kwargs)

        # Check that the method was called from the account payment view
        if context.get('allow_auto_lines', False):
            return res

        update_lines(res, line_dr_ids, line_cr_ids)

        return res

    def onchange_amount(self, cr, uid, ids, *args, **kwargs):

        context = kwargs.get('context', False) or args[-1]

        res = super(AccountVoucher, self).onchange_amount(
            cr, uid, ids, *args, **kwargs)

        # Check that the method was called from the account payment view
        if context.get('allow_auto_lines', False):
            return res

        if res.get('value', False):
            if res['value'].get('line_cr_ids', False):
                del res['value']['line_cr_ids']
            if res['value'].get('line_dr_ids', False):
                del res['value']['line_dr_ids']

        return res
