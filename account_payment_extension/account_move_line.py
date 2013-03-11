# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    AvanzOSC, Avanzed Open Source Consulting 
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
#    $Id$
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

import netsvc
from osv import fields, osv
from tools.translate import _

class account_move_line(osv.osv):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    def _invoice(self, cursor, user, ids, name, arg, context=None):
        invoice_obj = self.pool.get('account.invoice')
        res = {}
        for line_id in ids:
            res[line_id] = False
        cursor.execute('SELECT l.id, i.id ' \
                        'FROM account_move_line l, account_invoice i ' \
                        'WHERE l.move_id = i.move_id ' \
                        'AND l.id IN %s',
                        (tuple(ids),))
        invoice_ids = []
        
 
        for line_id, invoice_id in cursor.fetchall():
            res[line_id] = invoice_id
            invoice_ids.append(invoice_id)
        invoice_names = {False: ''}
        for invoice_id, name in invoice_obj.name_get(cursor, user, invoice_ids, context=context):
            invoice_names[invoice_id] = name
        for line_id in res.keys():
            invoice_id = res[line_id]
            res[line_id] = (invoice_id, invoice_names[invoice_id])
        
        for key in res.keys():
            if res[key][0] == False:   
            # if there is no a direct invoice related
                move_line_obj = self.pool.get('account.move.line')
                line1 = move_line_obj.browse(cursor, user, key)
                move = self.pool.get('account.move').browse (cursor, user, line1.move_id.id)
                
                if move:
                    for line_in in move.line_id:
                        if line_in.id <> key and (line_in.reconcile_id or line_in.reconcile_partial_id):
                            for line_in2 in line_in.reconcile_id.line_id:
                                if line_in2.id <> line_in.id:
                                    dict = self._invoice (cursor, user, [line_in2.id], name, arg, context)
                                    for item in dict.keys():
                                        res[key] = dict[item] 
                                    
        return res

    #===========================================================================
    # def _invoice(self, cr, uid, ids, name, arg, context=None):
    #    return super(account_move_line, self)._invoice(cr, uid, ids, name, arg, context)
    #===========================================================================

    def _invoice_search(self, cr, uid, obj, name, args, context={}):
        """ Redefinition for searching account move lines without any invoice related ('invoice.id','=',False)"""
        for x in args:
            if (x[2] is False) and (x[1] == '=') and (x[0] == 'invoice'):
                cr.execute('SELECT l.id FROM account_move_line l ' \
                    'LEFT JOIN account_invoice i ON l.move_id = i.move_id ' \
                    'WHERE i.id IS NULL', [])
                res = cr.fetchall()
                if not len(res):
                    return [('id', '=', '0')]
                return [('id', 'in', [x[0] for x in res])]
        return super(account_move_line, self)._invoice_search(cr, uid, obj, name, args, context=context)

    def amount_to_pay(self, cr, uid, ids, name, arg={}, context={}):
        """
        Return amount pending to be paid taking into account payment lines and the reconciliation.
        Note that the amount to pay can be due to negative supplier refund invoices or customer invoices.
        """

        if not ids:
            return {}
        cr.execute("""SELECT ml.id,
                    CASE WHEN ml.amount_currency < 0
                        THEN - ml.amount_currency
                        WHEN ml.amount_currency > 0
                        THEN ml.amount_currency
                        ELSE ml.credit - ml.debit
                    END AS debt,
                    (SELECT coalesce(sum(CASE WHEN pl.type='receivable' THEN -amount_currency ELSE amount_currency END),0)
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
                            COALESCE( SUM(COALESCE(amrl.credit,0) - COALESCE(amrl.debit,0)), 0 )
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

    def _to_pay_search(self, cr, uid, obj, name, args, context={}):
        if not len(args):
            return []
        currency = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.currency_id

        # For searching we first discard reconciled moves because the filter is fast and discards most records
        # quickly.
        ids = self.pool.get('account.move.line').search(cr, uid, [('reconcile_id','=',False)], context=context)
        records = self.pool.get('account.move.line').read(cr, uid, ids, ['id', 'amount_to_pay'], context)
        ids = []
        for record in records:
            if not self.pool.get('res.currency').is_zero( cr, uid, currency, record['amount_to_pay'] ):
                ids.append( record['id'] )
        if not ids:
            return [('id','=',False)]
        return [('id','in',ids)]

    def _payment_type_get(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        invoice_obj = self.pool.get('account.invoice')
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = (0,0)
            invoice_id = invoice_obj.search(cr, uid, [('move_id', '=', rec.move_id.id)], context=context)
            if invoice_id:
                inv = invoice_obj.browse(cr, uid, invoice_id[0], context)
                if inv.payment_type:
                    result[rec.id] = (inv.payment_type.id, self.pool.get('payment.type').browse(cr, uid, inv.payment_type.id, context).name)
            else:
                result[rec.id] = (0,0)
        return result

    def _payment_type_search(self, cr, uid, obj, name, args, context={}):
        if not len(args):
            return []
        operator = args[0][1]
        value = args[0][2]
        if not value:
            return []
        if isinstance(value, int) or isinstance(value, long):
            ids = [value]
        elif isinstance(value, list):
            ids = value 
        else:
            ids = self.pool.get('payment.type').search(cr,uid,[('name','ilike',value)], context=context)
        if ids:
            cr.execute('SELECT l.id ' \
                'FROM account_move_line l, account_invoice i ' \
                'WHERE l.move_id = i.move_id AND i.payment_type in (%s)' % (','.join(map(str, ids))))
            res = cr.fetchall()
            if len(res):
                return [('id', 'in', [x[0] for x in res])]
        return [('id','=','0')]

    _columns = {
        'invoice': fields.function(_invoice, method=True, string='Invoice',
            type='many2one', relation='account.invoice', fnct_search=_invoice_search),
        'received_check': fields.boolean('Received check', help="To write down that a check in paper support has been received, for example."),
        'partner_bank_id': fields.many2one('res.partner.bank','Bank Account'),
        'amount_to_pay' : fields.function(amount_to_pay, method=True, type='float', string='Amount to pay', fnct_search=_to_pay_search, store=True),
        'payment_type': fields.function(_payment_type_get, fnct_search=_payment_type_search, method=True, type="many2one", relation="payment.type", string="Payment type"),
    }

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        for key in vals.keys():
            if key not in ['received_check', 'partner_bank_id', 'date_maturity']:
                return super(account_move_line, self).write(cr, uid, ids, vals, context, check, update_check)
        return super(account_move_line, self).write(cr, uid, ids, vals, context, check, update_check=False)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False, submenu=False):
        menus = [
            self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_payment_extension', 'menu_action_invoice_payments'),
            #self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_payment_extension', 'menu_action_done_payments'),
        ]
        views = [
            self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_payment_extension', 'view_payments_tree'),
    
        ]
        
        menus = [m[1] for m in menus]
        views = [v[1] for v in views]
        #=======================================================================
        # if 'active_id' in context and context['active_id'] in menus:
        #    # Use standard views for account.move.line object
        #    if view_type == 'search':
        #        # Get a specific search view (bug in 6.0RC1, it does not give the search view defined in the action window)
        #        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_payment_extension', 'view_payments_filter')[1]
        #    result = super(osv.osv, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        # else:
        #    # Use special views for account.move.line object (for ex. tree view contains user defined fields)
        #    result = super(account_move_line, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        #=======================================================================
        if view_id in views:
            result = super(osv.osv, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        else:
            result = super(account_move_line, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
            
        return result
        
    def pay_move_lines(self, cr, uid, ids, context=None):
        
        #obj_move = self.pool.get('account.move')
        amount = 0
        name = ''
        ttype = ''
        invoice_type = ''
        partner_id = False
        inv_id = False 
        several_invoices = False
        if context is None:
            context = {}
        data_line = self.browse(cr, uid,ids, context)
        for line in data_line:
            #move_ids.append(line.move_id.id)
            if not inv_id:
                inv_id = line.invoice.id
            if inv_id and (line.invoice.id <> inv_id):
                several_invoices = True
            if partner_id and (line.partner_id.id <> partner_id):
                raise osv.except_osv(_('Warning'), _('The pay entries have to be for the same partner!!!'))
            else :
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
            
        print amount
            
        return {
            'name':_("Pay Moves"),
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
                'invoice_id':inv_id,
                'default_type': ttype ,
                'type':  ttype ,
                'move_line_ids': ids
                }
        }
account_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
