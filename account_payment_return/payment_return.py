# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2012 7 i TRIA <http://www.7itria.cat>
#    Copyright (c) 2011-2012 Avanzosc <http://www.avanzosc.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com> 
#    Copyright (c) 2014 initOS GmbH & Co. KG <http://initos.com/>
#                       Markus Schneider <markus.schneider at initos.com>
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
from osv import orm, fields
from tools.translate import _
import decimal_precision as dp
import time

class payment_order_return(orm.Model):
    _name = "payment.return"
    _inherit = ['mail.thread']
    _description = 'Payment return'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      help="Company",
                                      states={
                                              'done':[('readonly',True)],
                                              'cancelled':[('readonly',True)]
                                              }),
        'date' : fields.date('Return date',
                             help="This date will be used as the date for the "
                             "account entry.",
                             states={
                                     'done':[('readonly',True)],
                                     'cancelled':[('readonly',True)]
                                     }),
        'name' : fields.char("Reference", size=64, required=True,
                             states={
                                     'done':[('readonly',True)],
                                     'cancelled':[('readonly',True)]
                                     }),
        'period_id': fields.many2one('account.period', 'Forced period',
                                     states={
                                             'done':[('readonly',True)],
                                             'cancelled':[('readonly',True)]
                                             }),
        'lines_id' : fields.one2many('payment.return.line', 'return_id',
                                     states={
                                             'done':[('readonly',True)],
                                             'cancelled':[('readonly',True)]
                                             }),
        'journal_id': fields.many2one('account.journal', 'Bank journal',
                                      required=True,
                                      states={
                                              'done':[('readonly',True)],
                                              'cancelled':[('readonly',True)]
                                              }),
        'move_id': fields.many2one('account.move',
                                   'Reference to the created journal entry',
                                   states={
                                           'done':[('readonly',True)],
                                           'cancelled':[('readonly',True)]
                                           }),
        'notes' : fields.text('Notes'),
        'state' : fields.selection([
            ('draft', 'Draft'),
            ('imported', 'Imported'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled')
            ], 'State', readonly=True),
    }
    _track = {
        'state': {
            'account_payment_return.mt_payment_return_state_change': lambda self, cr, uid, obj, ctx=None: True,
        },
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account', context=c),
        'state': 'draft',
        'date': lambda *x: time.strftime('%Y-%m-%d %H:%M:%S'),
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').next_by_code(cr, uid, 'payment.return'),
    }

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        attachment_obj = self.pool.get('ir.attachment')
        for id in ids:
            # Remove file attachments (if any)
            id_at = attachment_obj.search(cr, uid, [
                        ('res_id', '=', id),
                        ('res_model', '=', 'payment.return'),
                    ], context=context)
            if id_at:
                attachment_obj.unlink(cr, uid, id_at, context)
        
        return super(payment_order_return, self).unlink(cr, uid, ids,
                                                        context=context)

    def action_confirm(self, cr, uid, ids, *args):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        reconcile_obj = self.pool.get('account.move.reconcile')
        return_line_obj = self.pool.get('payment.return.line')
        for payment_return in self.browse(cr, uid, ids):
            # Check for incomplete lines
            for return_line in payment_return.lines_id:
                if not return_line.invoice_id:
                    raise orm.except_orm(_('Error!'),
                        _("You must complete all invoice references in the "
                          "payment return."))

            move = {
                'name': '/',
                'ref': _('Return %s') %payment_return.name,
                'journal_id': payment_return.journal_id.id,
                'date': payment_return.date,
                'company_id': payment_return.company_id.id,
            }
            # Period
            if payment_return.period_id:
                move['period_id'] = payment_return.period_id.id
            else:
                move['period_id'] = self.pool.get('account.period').find(cr,
                    uid, dt=payment_return.date, 
                    context={'company_id': payment_return.company_id.id})[0]

            move_id = move_obj.create(cr, uid, move)

            for return_line in payment_return.lines_id:
                invoice = return_line.invoice_id
                # Select first credit line
                move_line = False
                for payment_move_line in invoice.payment_ids:
                    if payment_move_line.credit:
                        move_line = payment_move_line
                        break
                if move_line:
                    old_reconcile = move_line.reconcile_id
                    lines2reconcile = [x.id for x in old_reconcile.line_id]
                    move_line_id = move_line_obj.copy(
                        cr, uid, move_line.id,
                        {
                         'move_id': move_id,
                         'ref': move['ref'],
                         'date': move['date'],
                         'period_id': move['period_id'],
                         'journal_id': move['journal_id'],
                         'debit': return_line.amount,
                         'credit': 0,
                         })
                    lines2reconcile.append(move_line_id)
                    bank_move_line_id = move_line_obj.copy(
                        cr, uid, move_line_id,
                        {
                         'debit': 0,
                         'credit': return_line.amount,
                         'account_id': move_line.move_id.journal_id.default_credit_account_id.id,
                         })
                # Break old reconcile and make a new one with at least three moves
                reconcile_obj.unlink(cr, uid, [old_reconcile.id])
                move_line_obj.reconcile_partial(cr, uid, lines2reconcile)
                move_line = move_line_obj.browse(cr, uid, move_line_id)
                return_line_obj.write(cr, uid, return_line.id, 
                    {'reconcile_id': move_line.reconcile_partial_id.id})
                # Mark invoice as payment refused
                invoice_obj.write(cr, uid, [invoice.id],
                                  {'payment_returned': True})

            move_obj.button_validate(cr, uid, [move_id])
            self.write(cr, uid, payment_return.id,
                       {'state': 'done', 'move_id': move_id})
        return True

    def action_cancel(self, cr, uid, ids, *args):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        reconcile_obj = self.pool.get('account.move.reconcile')
        return_line_obj = self.pool.get('payment.return.line')
        for payment_return in self.browse(cr, uid, ids):
            if payment_return.move_id:
                for return_line in payment_return.lines_id:
                    if return_line.reconcile_id:
                        reconcile = return_line.reconcile_id
                        lines2reconcile = [x.id for x in
                                           reconcile.line_partial_ids if 
                                           x.move_id<>payment_return.move_id]
                        reconcile_obj.unlink(cr, uid, [reconcile.id])
                        move_line_obj.reconcile(cr, uid, lines2reconcile)
                        return_line_obj.write(cr, uid, return_line.id, 
                                              {'reconcile_id': False}
                                              )
                    # Remove payment refused flag on invoice
                    invoice_obj.write(cr, uid, [return_line.invoice_id.id],
                                      {'payment_returned': False})
                move_obj.button_cancel(cr, uid, [payment_return.move_id.id])
                move_obj.unlink(cr, uid, [payment_return.move_id.id])
        self.write(cr, uid, ids, {'state': 'cancelled', 'move_id': False})
        return True

    def action_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True


class payment_order_return_line(orm.Model):
    _name = "payment.return.line"
    _description = 'Payment return lines'
    
    _columns = {
        'return_id' : fields.many2one('payment.return', 'Payment return', 
            required=True, ondelete='cascade'),
        'concept': fields.char('Concept', size=100,
            help="Readed from imported file. Only for reference."),
        'reason' : fields.char('Return reason', size=100, 
            help="Readed from imported file. Only for reference."),
        'invoice_id': fields.many2one('account.invoice', 'Associated invoice'),
        'date' : fields.date('Return date',
            help="Readed from imported file. Only for reference."),
        'notes' : fields.text('Notes'),
        'partner_name': fields.char('Partner name', size=100,
            help="Readed from imported file. Only for reference."),
        'partner_id': fields.many2one('res.partner', 'Customer', 
            domain="[('customer', '=', True)]"),
        'amount': fields.float('Amount',
            help="Amount customer returns, can be different from invoice amount", 
            digits_compute= dp.get_precision('Account')),
        'reconcile_id': fields.many2one('account.move.reconcile', 'Reconcile', 
            help='Reference to the reconcile object.'),
    }

    _defaults = {
        'date': lambda *x: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
