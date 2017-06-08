# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class PaymentMode(models.Model):
    _name = 'payment.mode'
    _description = 'Payment Mode'

    @api.model
    def _default_type(self):
        return self.env.ref(
            'account_payment_order.'
            'manual_bank_tranfer', raise_if_not_found=False)\
            or self.env['payment.mode.type']

    name = fields.Char('Name', required=True, help='Mode of Payment')

    bank_id = fields.Many2one('res.partner.bank', "Bank account",
                              required=True,
                              help='Bank Account for the Payment Mode')

    journal_id = fields.Many2one('account.journal', 'Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))],
                                 help='Bank or Cash Journal for the '
                                 'Payment Mode', oldname='journal')

    company_id = fields.\
        Many2one('res.company', 'Company', required=True,
                 default=lambda self: self.env.user.company_id.id)

    partner_id = fields.Many2one('res.partner',
                                 related='company_id.partner_id',
                                 string='Partner', store=True)

    type = fields.Many2one(
        'payment.mode.type', string='Export type', required=True,
        help='Select the Export Payment Type for the Payment Mode.',
        default=_default_type)
    payment_order_type = fields.Selection(
        related='type.payment_order_type', readonly=True, string="Order Type",
        selection=[('payment', 'Payment'), ('debit', 'Debit')],
        help="This field, that comes from export type, determines if this "
             "mode can be selected for customers or suppliers.")
    active = fields.Boolean(string='Active', default=True)
    sale_ok = fields.Boolean(string='Selectable on sale operations',
                             default=True)
    purchase_ok = fields.Boolean(string='Selectable on purchase operations',
                                 default=True)
    note = fields.Text(string="Note", translate=True)
