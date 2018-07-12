# Copyright 2011-2012 7 i TRIA <http://www.7itria.cat>
# Copyright 2011-2012 Avanzosc <http://www.avanzosc.com>
# Copyright 2013 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2014 Markus Schneider <markus.schneider@initos.com>
# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import Warning as UserError
import odoo.addons.decimal_precision as dp


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
                _("Payment reference must be unique"
                  "\n%s") % '\n'.join(error_list)
            )

    def _get_move_amount(self, return_line):
        return return_line.amount

    def _prepare_invoice_returned_vals(self):
        return {'returned_payment': True}

    @api.multi
    def unlink(self):
        if self.filtered(lambda x: x.state == 'done'):
            raise UserError(_(
                "You can not remove a payment return if state is 'Done'"))
        return super(PaymentReturn, self).unlink()

    @api.multi
    def button_match(self):
        self.mapped('line_ids').filtered(lambda x: (
            (not x.move_line_ids) and x.reference))._find_match()
        self._check_duplicate_move_line()

    @api.multi
    def _prepare_return_move_vals(self):
        """Prepare the values for the journal entry created from the return.

        :return: Dictionary with the record values.
        """
        self.ensure_one()
        return {
            'name': '/',
            'ref': _('Return %s') % self.name,
            'journal_id': self.journal_id.id,
            'date': self.date,
            'company_id': self.company_id.id,
        }

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        # Check for incomplete lines
        if self.line_ids.filtered(lambda x: not x.move_line_ids):
            raise UserError(
                _("You must input all moves references in the payment "
                  "return."))
        invoices = self.env['account.invoice']
        move_line_obj = self.env['account.move.line']
        move = self.env['account.move'].create(
            self._prepare_return_move_vals()
        )
        total_amount = 0.0
        for return_line in self.line_ids:
            move_amount = self._get_move_amount(return_line)
            move_line2 = self.env['account.move.line'].with_context(
                check_move_validity=False).create({
                    'name': move.ref,
                    'debit': move_amount,
                    'credit': 0.0,
                    'account_id': return_line.move_line_ids[0].account_id.id,
                    'move_id': move.id,
                    'partner_id': return_line.partner_id.id,
                    'journal_id': move.journal_id.id,
                })
            total_amount += move_amount
            for move_line in return_line.move_line_ids:
                returned_moves = move_line.matched_debit_ids.mapped(
                    'debit_move_id')
                invoices |= returned_moves.mapped('invoice_id')
                move_line.remove_move_reconcile()
                (move_line | move_line2).reconcile()
                return_line.move_line_ids.mapped('matched_debit_ids').write(
                    {'origin_returned_move_ids': [(6, 0, returned_moves.ids)]})
            if return_line.expense_amount:
                expense_lines_vals = []
                expense_lines_vals.append({
                    'name': move.ref,
                    'move_id': move.id,
                    'debit': 0.0,
                    'credit': return_line.expense_amount,
                    'partner_id': return_line.expense_partner_id.id,
                    'account_id': (return_line.return_id.journal_id.
                                   default_credit_account_id.id),
                })
                expense_lines_vals.append({
                    'move_id': move.id,
                    'debit': return_line.expense_amount,
                    'name': move.ref,
                    'credit': 0.0,
                    'partner_id': return_line.expense_partner_id.id,
                    'account_id': return_line.expense_account.id,
                })
                for expense_line_vals in expense_lines_vals:
                    move_line_obj.with_context(
                        check_move_validity=False).create(expense_line_vals)
            extra_lines_vals = return_line._prepare_extra_move_lines(move)
            for extra_line_vals in extra_lines_vals:
                move_line_obj.create(extra_line_vals)
        move_line_obj.create({
            'name': move.ref,
            'debit': 0.0,
            'credit': total_amount,
            'account_id': self.journal_id.default_credit_account_id.id,
            'move_id': move.id,
            'journal_id': move.journal_id.id,
        })
        # Write directly because we returned payments just now
        invoices.write(self._prepare_invoice_returned_vals())
        move.post()
        self.write({'state': 'done', 'move_id': move.id})
        return True

    @api.multi
    def action_cancel(self):
        invoices = self.env['account.invoice']
        for move_line in self.mapped('move_id.line_ids').filtered(
                lambda x: x.user_type_id.type == 'receivable'):
            for partial_line in move_line.matched_credit_ids:
                invoices |= partial_line.origin_returned_move_ids.mapped(
                    'invoice_id')
                lines2reconcile = (partial_line.origin_returned_move_ids |
                                   partial_line.credit_move_id)
                partial_line.credit_move_id.remove_move_reconcile()
                lines2reconcile.reconcile()
        self.move_id.button_cancel()
        self.move_id.unlink()
        self.write({'state': 'cancelled', 'move_id': False})
        invoices.check_payment_return()
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
    reason_id = fields.Many2one(
        comodel_name='payment.return.reason',
        oldname="reason",
        string='Return reason',
    )
    reference = fields.Char(
        string='Reference',
        help="Reference to match moves from related documents")
    move_line_ids = fields.Many2many(
        comodel_name='account.move.line', string='Payment Reference')
    date = fields.Date(
        string='Return date', help="Only for reference",
    )
    partner_name = fields.Char(
        string='Partner name', readonly=True,
        help="Read from imported file. Only for reference.")
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer',
        domain="[('customer', '=', True)]")
    amount = fields.Float(
        string='Amount',
        help="Returned amount. Can be different from the move amount",
        digits=dp.get_precision('Account'))
    expense_account = fields.Many2one(
        comodel_name='account.account', string='Charges Account')
    expense_amount = fields.Float(string='Charges Amount')
    expense_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Charges Partner",
        domain=[('supplier', '=', True)],
    )

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
                    _("All payments must be owned by the same partner"))
            line.partner_id = partners[:1].id
            line.partner_name = partners[:1].name

    @api.onchange('move_line_ids')
    def _onchange_move_line(self):
        self._compute_amount()

    @api.onchange('expense_amount')
    def _onchange_expense_amount(self):
        if self.expense_amount:
            journal = self.return_id.journal_id
            self.expense_account = journal.default_expense_account_id
            self.expense_partner_id = journal.default_expense_partner_id

    @api.multi
    def match_invoice(self):
        for line in self:
            domain = line.partner_id and [
                ('partner_id', '=', line.partner_id.id)] or []
            domain.append(('number', '=', line.reference))
            invoice = self.env['account.invoice'].search(domain)
            if invoice:
                payments = invoice.payment_move_line_ids
                if payments:
                    line.move_line_ids = payments[0].ids
                    if not line.concept:
                        line.concept = _('Invoice: %s') % invoice.number

    @api.multi
    def match_move_lines(self):
        for line in self:
            domain = line.partner_id and [
                ('partner_id', '=', line.partner_id.id)] or []
            if line.return_id.journal_id:
                domain.append(('journal_id', '=',
                               line.return_id.journal_id.id))
            domain.extend([
                ('account_id.internal_type', '=', 'receivable'),
                ('reconciled', '=', True),
                '|',
                ('name', '=', line.reference),
                ('ref', '=', line.reference),
            ])
            move_lines = self.env['account.move.line'].search(domain)
            if move_lines:
                line.move_line_ids = move_lines.ids
                if not line.concept:
                    line.concept = (_('Move lines: %s') %
                                    ', '.join(move_lines.mapped('name')))

    @api.multi
    def match_move(self):
        for line in self:
            domain = line.partner_id and [
                ('partner_id', '=', line.partner_id.id)] or []
            domain.append(('name', '=', line.reference))
            move = self.env['account.move'].search(domain)
            if move:
                if len(move) > 1:
                    raise UserError(
                        _("More than one matches to move reference: %s") %
                        self.reference)
                line.move_line_ids = move.line_ids.filtered(lambda l: (
                    l.user_type_id.type == 'receivable' and l.reconciled
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

    @api.multi
    def _prepare_extra_move_lines(self, move):
        """Include possible extra lines in the return journal entry for other
        return concepts.

        :param self: Reference to the payment return line.
        :param move: Reference to the journal entry created for the return.
        :return: A list with dictionaries of the extra move lines to add
        """
        self.ensure_one()
        return []
