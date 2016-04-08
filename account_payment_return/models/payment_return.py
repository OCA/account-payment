# -*- coding: utf-8 -*-
# © 2011-2012 7 i TRIA <http://www.7itria.cat>
# © 2011-2012 Avanzosc <http://www.avanzosc.com>
# © 2013 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# © 2014 Markus Schneider <markus.schneider@initos.com>
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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

    @api.multi
    @api.constrains('line_ids')
    def _check_duplicate_move_line(self):
        def append_error(error_line):
            error_list.append(
                _("Payment Line: %s (%s) in Payment Return: %s") % (
                    ', '.join(error_line.mapped('move_line_ids.name')),
                    error_line.partner_id.name,
                    error_line.return_id.name
                )
            )
        error_list = []
        all_move_lines = self.env['account.move.line']
        for line in self.mapped('line_ids'):
            for move_line in line.move_line_ids:
                if move_line in all_move_lines:
                    append_error(line)
                all_move_lines |= move_line
        if (not error_list) and all_move_lines:
            duplicate_lines = self.env['payment.return.line'].search([
                ('move_line_ids', 'in', all_move_lines.ids),
                ('return_id.state', '=', 'done'),
            ])
            if duplicate_lines:
                for line in duplicate_lines:
                    append_error(line)
        if error_list:
            raise UserError(
                "Payment reference must be unique!\n"
                "%s" % '\n'.join(error_list)
            )

    def _get_invoices(self, move_lines):
        invoice_moves = move_lines.filtered('debit').mapped('move_id')
        invoices = self.env['account.invoice'].search(
            [('move_id', 'in', invoice_moves.ids)])
        return invoices

    def _get_move_amount(self, return_line, move_line):
        return return_line.amount

    def _prepare_invoice_returned_vals(self):
        return {'returned_payment': True}

    def _prepare_invoice_returned_cancel_vals(self):
        return {'returned_payment': False}

    @api.multi
    def button_match(self):
        self.mapped('line_ids').filtered(lambda x: (
            (not x.move_line_ids) and x.reference))._find_match()
        self._check_duplicate_move_line()

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        # Check for incomplete lines
        if self.line_ids.filtered(lambda x: not x.move_line_ids):
            raise UserError(
                _("You must input all moves references in the payment "
                  "return."))
        invoices_returned = self.env['account.invoice']
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
            lines2reconcile = return_line.move_line_ids.mapped(
                'reconcile_id.line_id')
            invoices_returned |= self._get_invoices(lines2reconcile)
            for move_line in return_line.move_line_ids:
                move_amount = self._get_move_amount(return_line, move_line)
                move_line2 = move_line.copy(
                    default={
                        'move_id': move_id.id,
                        'debit': move_amount,
                        'name': move['ref'],
                        'credit': 0,
                    })
                lines2reconcile |= move_line2
                move_line2.copy(
                    default={
                        'debit': 0,
                        'credit': move_amount,
                        'account_id':
                            self.journal_id.default_credit_account_id.id,
                    })
                # Break old reconcile
                move_line.reconcile_id.unlink()
            # Make a new one with at least three moves
            lines2reconcile.reconcile_partial()
            return_line.write(
                {'reconcile_id': move_line2.reconcile_partial_id.id})
        # Mark invoice as payment refused
        invoices_returned.write(self._prepare_invoice_returned_vals())
        move_id.button_validate()
        self.write({'state': 'done', 'move_id': move_id.id})
        return True

    @api.multi
    def action_cancel(self):
        self.ensure_one()
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
        invoices.write(self._prepare_invoice_returned_cancel_vals())
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
    reason = fields.Many2one(
        comodel_name='payment.return.reason',
        string='Return reason',
    )
    reference = fields.Char(
        string='Reference',
        help="Reference to match moves from related documents")
    move_line_ids = fields.Many2many(
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

    @api.multi
    def _compute_amount(self):
        for line in self:
            line.amount = sum(line.move_line_ids.mapped('credit'))

    @api.multi
    def _get_partner_from_move(self):
        for line in self.filtered(lambda x: not x.partner_id):
            partners = line.move_line_ids.mapped('partner_id')
            if len(partners) > 1:
                raise UserError(
                    "All payments must be owned by the same partner")
            line.partner_id = partners[:1].id
            line.partner_name = partners[:1].name

    @api.onchange('move_line_ids')
    def _onchange_move_line(self):
        self._compute_amount()

    @api.multi
    def match_invoice(self):
        for line in self:
            if line.partner_id:
                domain = [('partner_id', '=', line.partner_id.id)]
            else:
                domain = []
            domain.append(('number', '=', line.reference))
            invoice = self.env['account.invoice'].search(domain)
            if invoice:
                payments = invoice.payment_ids.filtered(
                    lambda x: x.credit > 0.0)
                if payments:
                    line.move_line_ids = payments[0].ids
                    if not line.concept:
                        line.concept = _('Invoice: %s') % invoice.number

    @api.multi
    def match_move_lines(self):
        for line in self:
            if line.partner_id:
                domain = [('partner_id', '=', line.partner_id.id)]
            else:
                domain = []
            domain += [
                ('account_id.type', '=', 'receivable'),
                ('credit', '>', 0.0),
                ('reconcile_ref', '!=', False),
                '|',
                ('name', '=', line.reference),
                ('ref', '=', line.reference),
            ]
            move_lines = self.env['account.move.line'].search(domain)
            if move_lines:
                line.move_line_ids = move_lines.ids
                if not line.concept:
                    line.concept = (_('Move lines: %s') %
                                    ', '.join(move_lines.mapped('name')))

    @api.multi
    def match_move(self):
        for line in self:
            if line.partner_id:
                domain = [('partner_id', '=', line.partner_id.id)]
            else:
                domain = []
            domain.append(('name', '=', line.reference))
            move = self.env['account.move'].search(domain)
            if move:
                if len(move) > 1:
                    raise UserError(
                        "More than one matches to move reference: %s" %
                        self.reference)
                line.move_line_ids = move.line_id.filtered(lambda l: (
                    l.account_id.type == 'receivable' and
                    l.credit > 0 and
                    l.reconcile_ref
                )).ids
                if not line.concept:
                    line.concept = _('Move: %s') % move.ref

    @api.multi
    def _find_match(self):
        # we filter again to remove all ready matched lines in inheritance
        lines2match = self.filtered(lambda x: (
            (not x.move_line_ids) and x.reference))
        lines2match.match_invoice()

        lines2match = lines2match.filtered(lambda x: (
            (not x.move_line_ids) and x.reference))
        lines2match.match_move_lines()

        lines2match = lines2match.filtered(lambda x: (
            (not x.move_line_ids) and x.reference))
        lines2match.match_move()
        self._get_partner_from_move()
        self.filtered(lambda x: not x.amount)._compute_amount()
