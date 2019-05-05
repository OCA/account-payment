# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import UserError


class AccountAbstractPayment(models.AbstractModel):
    _inherit = 'account.abstract.payment'

    payment_difference_handling = fields.Selection(
        selection_add=[('reconcile_multi_deduct',
                        'Mark invoice as fully paid (multi deduct)')],
    )

    @api.one
    def _check_deduction_amount(self):
        prec_digits = self.env.user.company_id.currency_id.decimal_places
        if self.payment_difference_handling == 'reconcile_multi_deduct':
            if float_compare(self.payment_difference,
                             sum(self.deduction_ids.mapped('amount')),
                             precision_digits=prec_digits) != 0:
                raise UserError(_('The total deduction should be %s') %
                                self.payment_difference)

    @api.multi
    def _compute_deduct_residual(self):
        for rec in self:
            rec.deduct_residual = (rec.payment_difference -
                                   sum(rec.deduction_ids.mapped('amount')))


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    deduct_residual = fields.Monetary(
        string='Remainings',
        compute='_compute_deduct_residual',
    )
    deduction_ids = fields.One2many(
        comodel_name='account.payment.deduction',
        inverse_name='payment_id',
        string='Deductions',
        copy=False,
        help="Sum of deduction amount(s) must equal to the payment difference",
    )

    @api.one
    @api.constrains('deduction_ids')
    def _check_deduction_amount(self):
        super()._check_deduction_amount()

    @api.multi
    @api.depends('payment_difference', 'deduction_ids')
    def _compute_deduct_residual(self):
        super()._compute_deduct_residual()

    def _create_payment_entry(self, amount):
        """ If choosing new payment handling payment_difference_handling,
        otherwise, fall back to original _create_payment_entry() """
        if self.payment_difference_handling == 'reconcile_multi_deduct':
            return self._create_payment_entry_multi_deduct(amount)
        else:
            return super()._create_payment_entry(amount)

    def _create_payment_entry_multi_deduct(self, amount):
        """ Create payment entry for multi deduction,
        similar to _create_payment_entry, but with multiple writeoff """
        MoveLine = self.env['account.move.line'].\
            with_context(check_move_validity=False)
        debit, credit, amount_currency, currency_id = \
            MoveLine.with_context(date=self.payment_date).\
            _compute_amount_fields(amount, self.currency_id,
                                   self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        # Write line corresponding to invoice payment
        counterpart_aml_dict = \
            self._get_shared_move_line_vals(debit, credit,
                                            amount_currency, move.id, False)
        counterpart_aml_dict.update(
            self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = MoveLine.create(counterpart_aml_dict)

        # Reconcile with the invoices
        if self.payment_difference:
            for deduct in self.deduction_ids:
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0,
                                                                move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = \
                    MoveLine.with_context(date=self.payment_date).\
                    _compute_amount_fields(deduct.amount,
                                           self.currency_id,
                                           self.company_id.currency_id)
                writeoff_line['name'] = deduct.name
                writeoff_line['account_id'] = deduct.account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = MoveLine.create(writeoff_line)
                if counterpart_aml['debit'] or (writeoff_line['credit'] and
                                                not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and
                                                 not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo

        # Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(
                credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(
                self._get_liquidity_move_line_vals(-amount))
            MoveLine.create(liquidity_aml_dict)

        # validate the payment
        if not self.journal_id.post_at_bank_rec:
            move.post()

        # reconcile the invoice receivable/payable line(s) with the payment
        if self.invoice_ids:
            self.invoice_ids.register_payment(counterpart_aml)

        return move


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.register.payments'

    deduct_residual = fields.Monetary(
        string='Remainings',
        compute='_compute_deduct_residual',
    )
    deduction_ids = fields.One2many(
        comodel_name='account.register.payment.deduction',
        inverse_name='payment_id',
        string='Deductions',
        copy=False,
        help="Sum of deduction amount(s) must equal to the payment difference",
    )

    @api.one
    @api.constrains('deduction_ids')
    def _check_deduction_amount(self):
        super()._check_deduction_amount()

    @api.multi
    @api.depends('payment_difference', 'deduction_ids')
    def _compute_deduct_residual(self):
        super()._compute_deduct_residual()

    @api.multi
    def _prepare_payment_vals(self, invoices):
        values = super()._prepare_payment_vals(invoices)
        values['deduction_ids'] = [
            (0, 0, {'account_id': x.account_id.id,
                    'amount': x.amount,
                    'name': x.name, })
            for x in self.deduction_ids
        ]
        return values


class AccountPaymentDeduction(models.Model):
    _name = 'account.payment.deduction'
    _description = 'Payment Deduction'

    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string='Payment',
        readonly=True,
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='payment_id.currency_id',
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        domain=[('deprecated', '=', False)],
        required=True,
    )
    amount = fields.Monetary(
        string='Deduction Amount',
        required=True,
    )
    name = fields.Char(
        string='Label',
        required=True,
    )


class AccountRegisterPaymentDeduction(models.TransientModel):
    _name = 'account.register.payment.deduction'
    _description = 'Payment Deduction'

    payment_id = fields.Many2one(
        comodel_name='account.register.payments',
        string='Payment',
        readonly=True,
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='payment_id.currency_id',
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        domain=[('deprecated', '=', False)],
        required=True,
    )
    amount = fields.Monetary(
        string='Deduction Amount',
        required=True,
    )
    name = fields.Char(
        string='Label',
        required=True,
    )
