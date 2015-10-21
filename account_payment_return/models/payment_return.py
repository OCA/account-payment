# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2012 7 i TRIA <http://www.7itria.cat>
#    Copyright (c) 2011-2012 Avanzosc <http://www.avanzosc.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados <http://www.serviciosbaeza.com>
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2014 initOS GmbH & Co. KG <http://initos.com/>
#                       Markus Schneider <markus.schneider at initos.com>
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
from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
import openerp.addons.decimal_precision as dp


class PaymentReturn(models.Model):
    _name = "payment.return"
    _inherit = ['mail.thread']
    _description = 'Payment return'
    _order = 'date DESC, id DESC'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        states={'done': [('readonly', True)],
                'cancelled': [('readonly', True)]},
        default=lambda self: self.env['res.company']._company_default_get(
            'account'))
    date = fields.Date(
        string='Return date',
        help="This date will be used as the account entry date.",
        states={'done': [('readonly', True)],
                'cancelled': [('readonly', True)]},
        default=lambda x: fields.Date.today())
    name = fields.Char(
        string="Reference", required=True,
        states={'done': [('readonly', True)],
                'cancelled': [('readonly', True)]},
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'payment.return'))
    period_id = fields.Many2one(
        comodel_name='account.period', string='Forced period',
        states={'done': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    line_ids = fields.One2many(
        comodel_name='payment.return.line', inverse_name='return_id',
        states={'done': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    journal_id = fields.Many2one(
        comodel_name='account.journal', string='Bank journal', required=True,
        states={'done': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Reference to the created journal entry',
        states={'done': [('readonly', True)],
                'cancelled': [('readonly', True)]})
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('imported', 'Imported'),
                   ('done', 'Done'),
                   ('cancelled', 'Cancelled')],
        string='State', readonly=True, default='draft',
        track_visibility='onchange')

    def _get_invoices(self, move_lines):
        invoice_moves = self.env['account.move']
        for invoice_move_line in move_lines.filtered('debit'):
            invoice_moves += invoice_move_line.move_id
        invoices = self.env['account.invoice'].search(
            [('move_id', 'in', invoice_moves.ids)])
        return invoices

    @api.one
    def action_confirm(self):
        # Check for incomplete lines
        if any(not x.move_line_id for x in self.line_ids):
            raise UserError(
                _("You must input all moves references in the payment "
                  "return."))
        move = {
            'name': '/',
            'ref': _('Return %s') % self.name,
            'journal_id': self.journal_id.id,
            'date': self.date,
            'company_id': self.company_id.id,
            'period_id': (self.period_id.id or self.period_id.with_context(
                company_id=self.company_id.id).find(self.date).id),
        }
        move_id = self.env['account.move'].create(move)
        for return_line in self.line_ids:
            move_line = return_line.move_line_id
            old_reconcile = move_line.reconcile_id
            lines2reconcile = old_reconcile.line_id
            invoices = self._get_invoices(lines2reconcile)
            move_line2 = move_line.copy(
                default={
                    'move_id': move_id.id,
                    'debit': return_line.amount,
                    'name': move['ref'],
                    'credit': 0,
                })
            lines2reconcile += move_line2
            move_line2.copy(
                default={
                    'debit': 0,
                    'credit': return_line.amount,
                    'account_id': self.journal_id.default_credit_account_id.id,
                })
            # Break old reconcile and
            # make a new one with at least three moves
            old_reconcile.unlink()
            lines2reconcile.reconcile_partial()
            return_line.write(
                {'reconcile_id': move_line2.reconcile_partial_id.id})
            # Mark invoice as payment refused
            invoices.write({'returned_payment': True})
        move_id.button_validate()
        self.write({'state': 'done', 'move_id': move_id.id})
        return True

    @api.one
    def action_cancel(self):
        if not self.move_id:
            return True
        for return_line in self.line_ids:
            invoices = self.env['account.invoice']
            if return_line.reconcile_id:
                reconcile = return_line.reconcile_id
                lines2reconcile = reconcile.line_partial_ids.filtered(
                    lambda x: x.move_id != self.move_id)
                invoices = self._get_invoices(lines2reconcile)
                reconcile.unlink()
                if lines2reconcile:
                    lines2reconcile.reconcile()
                return_line.write({'reconcile_id': False})
            # Remove payment refused flag on invoice
            invoices.write({'returned_payment': False})
        self.move_id.button_cancel()
        self.move_id.unlink()
        self.write({'state': 'cancelled', 'move_id': False})
        return True

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True


class PaymentReturnLine(models.Model):
    _name = "payment.return.line"
    _description = 'Payment return lines'

    return_id = fields.Many2one(
        comodel_name='payment.return', string='Payment return',
        required=True, ondelete='cascade')
    concept = fields.Char(
        string='Concept',
        help="Read from imported file. Only for reference.")
    reason = fields.Char(
        string='Return reason', readonly=True,
        help="Read from imported file. Only for reference.")
    move_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Payment Reference')
    date = fields.Date(
        string='Return date', readonly=True,
        help="Read from imported file. Only for reference.",
        default=lambda x: fields.Date.today())
    partner_name = fields.Char(
        string='Partner name', readonly=True,
        help="Read from imported file. Only for reference.")
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer',
        domain="[('customer', '=', True)]")
    amount = fields.Float(
        string='Amount',
        help="Returned amount. Can be different from the move amount",
        digits_compute=dp.get_precision('Account'))
    reconcile_id = fields.Many2one(
        comodel_name='account.move.reconcile', string='Reconcile',
        help="Reference to the reconcile object.")

    @api.onchange('move_line_id')
    def onchange_move_line(self):
        self.amount = self.move_line_id.credit
