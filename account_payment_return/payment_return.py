# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2012 7 i TRIA <http://www.7itria.cat>
#    Copyright (c) 2011-2012 Avanzosc <http://www.avanzosc.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados <http://www.serviciosbaeza.com>
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2014 initOS GmbH & Co. KG <http://initos.com/>
#                       Markus Schneider <markus.schneider at initos.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
import time


class payment_return(orm.Model):
    _name = "payment.return"
    _inherit = ['mail.thread']
    _description = 'Payment return'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      help="Company",
                                      states={'done': [('readonly', True)],
                                              'cancelled': [('readonly', True)]
                                              }),
        'date': fields.date('Return date',
                            help="This date will be used as the date for the "
                                 "account entry.",
                            states={'done': [('readonly', True)],
                                    'cancelled': [('readonly', True)]
                                    }),
        'name': fields.char("Reference", size=64, required=True,
                            states={'done': [('readonly', True)],
                                    'cancelled': [('readonly', True)]
                                    }),
        'period_id': fields.many2one('account.period', 'Forced period',
                                     states={'done': [('readonly', True)],
                                             'cancelled': [('readonly', True)]
                                             }),
        'lines_id': fields.one2many('payment.return.line', 'return_id',
                                    states={'done': [('readonly', True)],
                                            'cancelled': [('readonly', True)]
                                            }),
        'journal_id': fields.many2one('account.journal', 'Bank journal',
                                      required=True,
                                      states={'done': [('readonly', True)],
                                              'cancelled': [('readonly', True)]
                                              }),
        'move_id': fields.many2one('account.move',
                                   'Reference to the created journal entry',
                                   states={'done': [('readonly', True)],
                                           'cancelled': [('readonly', True)]
                                           }),
        'notes': fields.text('Notes'),
        'state': fields.selection([
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
            id_at = attachment_obj.search(cr, uid, [('res_id', '=', id),
                                                    ('res_model', '=',
                                                     'payment.return'),
                                                    ], context=context)
            if id_at:
                attachment_obj.unlink(cr, uid, id_at, context)

        return super(payment_return, self).unlink(cr, uid, ids,
                                                  context=context)

    def action_confirm(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        reconcile_obj = self.pool.get('account.move.reconcile')
        return_line_obj = self.pool.get('payment.return.line')
        for payment_return in self.browse(cr, uid, ids, context=context):
            # Check for incomplete lines
            for return_line in payment_return.lines_id:
                if not return_line.invoice_id:
                    raise orm.except_orm(_('Error!'),
                                         _("You must complete all invoice "
                                           "references in the "
                                           "payment return."))

            move = {
                'name': '/',
                'ref': _('Return %s') % payment_return.name,
                'journal_id': payment_return.journal_id.id,
                'date': payment_return.date,
                'company_id': payment_return.company_id.id,
            }
            # Period
            if payment_return.period_id:
                move['period_id'] = payment_return.period_id.id
            else:
                context_move = context.copy()
                context_move.update({'company_id':
                                     payment_return.company_id.id})
                move['period_id'] = self.pool.get('account.period')\
                    .find(cr, uid, dt=payment_return.date,
                          context=context_move)[0]

            move_id = move_obj.create(cr, uid, move, context=context)

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
                        default={
                            'move_id': move_id,
                            'ref': move['ref'],
                            'date': move['date'],
                            'period_id': move['period_id'],
                            'journal_id': move['journal_id'],
                            'debit': return_line.amount,
                            'credit': 0,
                            }, context=context)
                    lines2reconcile.append(move_line_id)
                    move_line_obj.copy(
                        cr, uid, move_line_id,
                        default={
                            'debit': 0,
                            'credit': return_line.amount,
                            'account_id': move_line.move_id.journal_id
                            .default_credit_account_id.id,
                            }, context=context)
                # Break old reconcile and
                # make a new one with at least three moves
                reconcile_obj.unlink(cr, uid, [old_reconcile.id],
                                     context=context)
                move_line_obj.reconcile_partial(cr, uid, lines2reconcile,
                                                context=context)
                move_line = move_line_obj.browse(cr, uid, move_line_id,
                                                 context=context)
                return_line_obj.write(cr, uid, return_line.id,
                                      {'reconcile_id': move_line
                                       .reconcile_partial_id.id},
                                      context=context)
                # Mark invoice as payment refused
                invoice_obj.write(cr, uid, [invoice.id],
                                  {'payment_returned': True}, context=context)

            move_obj.button_validate(cr, uid, [move_id], context=context)
            self.write(cr, uid, payment_return.id,
                       {'state': 'done', 'move_id': move_id}, context=context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        reconcile_obj = self.pool.get('account.move.reconcile')
        return_line_obj = self.pool.get('payment.return.line')
        for payment_return in self.browse(cr, uid, ids, context=context):
            if payment_return.move_id:
                for return_line in payment_return.lines_id:
                    if return_line.reconcile_id:
                        reconcile = return_line.reconcile_id
                        lines2reconcile = [x.id for x in
                                           reconcile.line_partial_ids if
                                           x.move_id != payment_return.move_id]
                        reconcile_obj.unlink(cr, uid, [reconcile.id],
                                             context=context)
                        move_line_obj.reconcile(cr, uid, lines2reconcile,
                                                context=context)
                        return_line_obj.write(cr, uid, return_line.id,
                                              {'reconcile_id': False},
                                              context=context
                                              )
                    # Remove payment refused flag on invoice
                    invoice_obj.write(cr, uid, [return_line.invoice_id.id],
                                      {'payment_returned': False},
                                      context=context)
                move_obj.button_cancel(cr, uid, [payment_return.move_id.id],
                                       context=context)
                move_obj.unlink(cr, uid, [payment_return.move_id.id],
                                context=context)
        self.write(cr, uid, ids, {'state': 'cancelled', 'move_id': False},
                   context=context)
        return True

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True
