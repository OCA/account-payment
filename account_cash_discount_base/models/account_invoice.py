# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

READONLY_STATES = {
    'draft': [('readonly', False)],
}
DISCOUNT_ALLOWED_TYPES = (
    'in_invoice',
    'in_refund',
)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    discount_percent = fields.Float(
        string="Discount (%)",
        readonly=True,
        states=READONLY_STATES,
        digits=dp.get_precision('Discount'),
    )
    amount_total_with_discount = fields.Monetary(
        string="Total (with discount)",
        compute='_compute_amount_total_with_discount',
        store=True,
    )
    residual_with_discount = fields.Monetary(
        compute='_compute_residual_with_discount'
    )
    discount_amount = fields.Monetary(
        compute='_compute_discount_amount',
        store=True,
    )
    real_discount_amount = fields.Monetary(
        compute='_compute_real_discount_amount',
        string="Discount amount (minus related refunds amount)",
    )
    refunds_discount_amount = fields.Monetary(
        compute='_compute_refunds_discount_amount',
        store=True,
    )
    discount_delay = fields.Integer(
        string="Discount Delay (days)",
        readonly=True,
        states=READONLY_STATES
    )
    discount_due_date = fields.Date(
        readonly=True,
        states=READONLY_STATES
    )
    discount_due_date_readonly = fields.Date(
        string="Discount Due Date",
        compute='_compute_discount_due_date',
    )
    has_discount = fields.Boolean(
        compute='_compute_has_discount',
        store=True,
    )
    discount_base_date = fields.Date(
        compute='_compute_discount_base_date',
    )

    @api.multi
    @api.depends(
        'amount_total',
        'amount_untaxed',
        'discount_percent',
        'company_id',
    )
    def _compute_discount_amount(self):
        for rec in self:
            discount_amount = 0.0
            if rec.discount_percent != 0.0:
                base_amount_type = \
                    rec.company_id.cash_discount_base_amount_type
                base_amount = (
                    base_amount_type == 'untaxed' and
                    rec.amount_untaxed or rec.amount_total)
                discount_amount = base_amount * (rec.discount_percent / 100)
            rec.discount_amount = discount_amount

    @api.multi
    @api.depends(
        'amount_total',
        'refunds_discount_amount',
        'residual',
    )
    def _compute_residual_with_discount(self):
        for rec in self:
            rec.residual_with_discount = (
                rec.residual -
                rec.discount_amount +
                rec.refunds_discount_amount
            )

    @api.multi
    @api.depends(
        'amount_total',
        'payment_move_line_ids.debit',
        'payment_move_line_ids.credit',
        'payment_move_line_ids.invoice_id.discount_amount',
        'payment_move_line_ids.invoice_id.type',
    )
    def _compute_refunds_discount_amount(self):
        for rec in self:
            refunds_discount_total = 0.0
            for pmove_line in rec.payment_move_line_ids:
                pmove_line_inv = pmove_line.invoice_id
                if pmove_line_inv and pmove_line_inv.type == 'in_refund':
                    refunds_discount_total += pmove_line_inv.discount_amount
            rec.refunds_discount_amount = refunds_discount_total

    @api.multi
    @api.depends(
        'discount_amount',
        'refunds_discount_amount',
    )
    def _compute_real_discount_amount(self):
        for rec in self:
            rec.real_discount_amount = (
                rec.discount_amount -
                rec.refunds_discount_amount
            )

    @api.multi
    @api.depends(
        'amount_total',
        'discount_amount',
    )
    def _compute_amount_total_with_discount(self):
        for rec in self:
            rec.amount_total_with_discount = \
                rec.amount_total - rec.discount_amount

    @api.multi
    @api.depends(
        'discount_due_date',
    )
    def _compute_discount_due_date(self):
        for rec in self:
            rec.discount_due_date_readonly = rec.discount_due_date

    @api.multi
    @api.depends(
        'discount_amount',
        'discount_due_date',
    )
    def _compute_has_discount(self):
        for rec in self:
            rec.has_discount = (
                rec.discount_amount != 0 and
                rec.discount_due_date != 0 and
                rec.type in DISCOUNT_ALLOWED_TYPES
            )

    @api.multi
    @api.depends('date_invoice')
    def _compute_discount_base_date(self):
        for rec in self:
            if rec.date_invoice:
                rec.discount_base_date = rec.date_invoice
            else:
                rec.discount_base_date = fields.Date.context_today(rec)

    @api.multi
    @api.onchange(
        'has_discount',
        'discount_base_date',
        'discount_amount',
        'discount_delay',
    )
    def _onchange_discount_delay(self):
        for rec in self:
            skip = (
                rec.discount_amount == 0 or
                rec.discount_delay == 0 or
                rec.type not in DISCOUNT_ALLOWED_TYPES
            )
            if skip:
                continue
            discount_base_date = fields.Date.from_string(
                rec.discount_base_date)
            due_date = discount_base_date + timedelta(days=rec.discount_delay)
            rec.discount_due_date = due_date

    @api.onchange(
        'partner_id',
        'company_id',
    )
    def _onchange_partner_id(self):
        old_payment_term_id = self.payment_term_id
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.payment_term_id != old_payment_term_id:
            # be sure to load discount options based on the payment term.
            # It was not loaded when creating a vendor bill from a purchase
            # order.
            self._onchange_payment_term_discount_options()
        return res

    @api.multi
    @api.onchange(
        'payment_term_id',
    )
    def _onchange_payment_term_discount_options(self):
        payment_term = self.payment_term_id
        if payment_term and self.type in DISCOUNT_ALLOWED_TYPES:
            self.discount_percent = payment_term.discount_percent
            self.discount_delay = payment_term.discount_delay

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            inv._onchange_discount_delay()
            if not inv.discount_due_date and inv.discount_amount != 0.0:
                raise UserError(_(
                    "You can't set a discount amount if there is no "
                    "discount due date. (Invoice ID: %s)"
                ) % (inv.id,))
        return res

    @api.model
    def _prepare_refund(
            self, invoice, date_invoice=None, date=None, description=None,
            journal_id=None):
        values = super(AccountInvoice, self)._prepare_refund(
            invoice,
            date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id
        )

        partner_id = values.get('partner_id')
        if invoice.type in DISCOUNT_ALLOWED_TYPES and partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            payment_term = partner.property_supplier_payment_term_id
            values['payment_term_id'] = payment_term.id
        return values

    @api.multi
    @api.returns('self')
    def refund(
            self, date_invoice=None, date=None, description=None,
            journal_id=None):
        invoice = super(AccountInvoice, self).refund(
            date_invoice=date_invoice, date=date, description=description,
            journal_id=journal_id
        )
        invoice._onchange_payment_term_discount_options()
        invoice._onchange_discount_delay()
        return invoice
