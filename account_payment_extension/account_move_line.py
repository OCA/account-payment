# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    AvanzOSC, Avanzed Open Source Consulting
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, orm
from tools.translate import _


class AccountMoveLine(orm.Model):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    def _invoice(self, cursor, user, ids, name, arg, context=None):
        invoice_obj = self.pool['account.invoice']
        res = {}
        for line_id in ids:
            res[line_id] = False
        cursor.execute(
            'SELECT l.id, i.id '
            'FROM account_invoice i,account_move_line l '
            'left join account_move_line r on '
            '    l.reconcile_id=r.reconcile_id and l.id<>r.id '
            'left join account_move_line p on '
            '    l.reconcile_partial_id=p.reconcile_partial_id and l.id<>p.id '
            'where (i.move_id = l.move_id or i.move_id = r.move_id or '
            '    i.move_id = p.move_id) '
            '    AND l.id IN %s',
            (tuple(ids),))
        for line_id, invoice_id in cursor.fetchall():
            name = invoice_obj.name_get(cursor, user, [invoice_id],
                                        context=context)
            res[line_id] = name and name[0] or False
        return res

    def _invoice_search(self, cr, uid, obj, name, args, context=None):
        """ Redefinition for searching account move lines without any invoice
        related ('invoice.id','=',False)"""
        for x in args:
            if (x[2] is False) and (x[1] == '=') and (x[0] == 'invoice'):
                cr.execute(
                    'SELECT l.id FROM account_move_line l '
                    'LEFT JOIN account_invoice i ON l.move_id = i.move_id '
                    'WHERE i.id IS NULL', [])
                res = cr.fetchall()
                if not len(res):
                    return [('id', '=', '0')]
                return [('id', 'in', [x[0] for x in res])]
        return super(AccountMoveLine, self)._invoice_search(
            cr, uid, obj, name, args, context=context)

    def amount_to_pay(self, cr, uid, ids, name, arg={}, context=None):
        """Return amount pending to be paid taking into account payment lines
        and the reconciliation. Note that the amount to pay can be due to
        negative supplier refund invoices or customer invoices.
        """
        if not ids:
            return {}
        cr.execute(
            """SELECT ml.id,
                CASE WHEN ml.amount_currency < 0
                    THEN - ml.amount_currency
                    WHEN ml.amount_currency > 0
                    THEN ml.amount_currency
                    ELSE ml.credit - ml.debit
                END AS debt,
                (SELECT coalesce(sum(CASE WHEN pl.type='receivable' THEN
                -amount_currency ELSE amount_currency END),0)
                    FROM payment_line pl
                        INNER JOIN payment_order po
                            ON (pl.order_id = po.id)
                    WHERE
                        pl.move_line_id = ml.id AND
                        pl.payment_move_id IS NULL AND
                        po.state != 'cancel'
                ) AS paid,
                (
                    SELECT
                        COALESCE( SUM(COALESCE(amrl.credit,0) -
                        COALESCE(amrl.debit,0)), 0 )
                    FROM
                        account_move_reconcile amr,
                        account_move_line amrl
                    WHERE
                        amr.id = amrl.reconcile_partial_id AND
                        amr.id = ml.reconcile_partial_id
                ) AS unreconciled,
                reconcile_id
                FROM account_move_line ml
                WHERE id in (%s)""" % (",".join([str(int(x)) for x in ids])))
        result = {}
        for record in cr.fetchall():
            id = record[0]
            debt = record[1] or 0.0
            paid = record[2]
            unreconciled = record[3]
            reconcile_id = record[4]
            if reconcile_id:
                debt = 0.0
            else:
                if not unreconciled:
                    unreconciled = debt
                if debt > 0:
                    debt = min(debt - paid, max(0.0, unreconciled))
                else:
                    debt = max(debt - paid, min(0.0, unreconciled))
            result[id] = debt
        return result

    def _payment_type_get(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        invoice_obj = self.pool['account.invoice']
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = False
            invoice_ids = invoice_obj.search(
                cr, uid, [('move_id', '=', rec.move_id.id)], context=context)
            if invoice_ids:
                inv = invoice_obj.browse(cr, uid, invoice_ids[0], context)
                if inv.payment_type:
                    result[rec.id] = inv.payment_type.id
        return result

    def _get_move_lines_invoice(self, cr, uid, ids, context=None):
        result = set()
        invoice_obj = self.pool['account.invoice']
        for invoice in invoice_obj.browse(cr, uid, ids, context=context):
            if invoice.move_id:
                result.add(invoice.move_id.id)
        return list(result)

    def _get_move_lines(self, cr, uid, ids, context=None):
        result = set()
        line_obj = self.pool['payment.line']
        for line in line_obj.browse(cr, uid, ids, context=context):
            result.add(line.move_line_id.id)
            result.add(line.payment_move_id.id)
        return list(result)

    def _get_move_lines_order(self, cr, uid, ids, context=None):
        result = set()
        order_obj = self.pool['payment.order']
        for order in order_obj.browse(cr, uid, ids, context=context):
            for line in order.line_ids:
                result.add(line.move_line_id.id)
                result.add(line.payment_move_id.id)
        return list(result)

    def _get_reconcile(self, cr, uid, ids, context=None):
        result = set()
        reconcile_obj = self.pool['account.move.reconcile']
        for reconcile in reconcile_obj.browse(cr, uid, ids, context=context):
            for line in reconcile.line_id:
                result.add(line.id)
            for line in reconcile.line_partial_ids:
                result.add(line.id)
        return list(result)

    _columns = {
        'invoice': fields.function(
            _invoice, method=True, string='Invoice', type='many2one',
            relation='account.invoice', fnct_search=_invoice_search),
        'received_check': fields.boolean(
            'Received check',
            help="To write down that a check in paper support has been "
                 "received, for example."),
        'partner_bank_id': fields.many2one('res.partner.bank', 'Bank Account'),
        'amount_to_pay': fields.function(
            amount_to_pay, method=True,
            type='float', string='Amount to pay',
            store={
                'account.move.line': (lambda self, cr, uid, ids, context=None:
                                      ids, None, 20),
                'payment.order': (_get_move_lines_order, ['line_ids'], 20),
                'payment.line': (_get_move_lines,
                                 ['type', 'move_line_id', 'payment_move_id'],
                                 20),
                'account.move.reconcile': (_get_reconcile,
                                           ['line_id', 'line_partial_ids'], 20)
            }),
        'payment_type': fields.function(
            _payment_type_get, method=True, type="many2one",
            relation="payment.type", string="Payment type",
            store={
                'account.invoice': (_get_move_lines_invoice,
                                    ['payment_type'], 20),
            })
    }

    def write(self, cr, uid, ids, vals, context=None, check=True,
              update_check=True):
        for key in vals.keys():
            if key not in ['received_check', 'partner_bank_id',
                           'date_maturity']:
                return super(AccountMoveLine, self).write(
                    cr, uid, ids, vals, context, check, update_check)
        return super(AccountMoveLine, self).write(
            cr, uid, ids, vals, context, check, update_check=False)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        views = [
            self.pool['ir.model.data'].get_object_reference(
                cr, uid, 'account_payment_extension', 'view_payments_tree'),

        ]
        views = [v[1] for v in views]
        if view_id in views:
            result = super(orm.Model, self).fields_view_get(
                cr, uid, view_id, view_type, context, toolbar=toolbar,
                submenu=submenu)
        else:
            result = super(AccountMoveLine, self).fields_view_get(
                cr, uid, view_id, view_type, context, toolbar=toolbar,
                submenu=submenu)

        return result

    def pay_move_lines(self, cr, uid, ids, context=None):
        # obj_move = self.pool.get('account.move')
        amount = 0
        name = ''
        ttype = ''
        invoice_type = ''
        partner_id = False
        inv_id = False
        several_invoices = False
        data_line = self.browse(cr, uid, ids, context)
        for line in data_line:
            # move_ids.append(line.move_id.id)
            if not inv_id:
                inv_id = line.invoice.id
            if inv_id and (line.invoice.id != inv_id):
                several_invoices = True
            if partner_id and (line.partner_id.id != partner_id):
                raise orm.except_orm(
                    _('Warning'),
                    _('The pay entries have to be for the same partner!!!'))
            else:
                amount += line.amount_to_pay
                partner_id = line.partner_id.id
                name += line.name + '/'
        if several_invoices:
            inv_id = False
        if amount > 0:
            ttype = 'payment'
            invoice_type = 'in_invoice'
        else:
            amount = -amount
            ttype = 'receipt'
            invoice_type = 'out_invoice'
        return {
            'name': _("Pay Moves"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': {
                'default_partner_id': partner_id,
                'default_amount': amount,
                'default_name': name,
                'close_after_process': True,
                'invoice_type': invoice_type,
                'invoice_id': inv_id,
                'default_type': ttype,
                'type': ttype,
                'move_line_ids': ids,
            }
        }
