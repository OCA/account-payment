# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class PaymentModeType(models.Model):
    _name = 'payment.mode.type'
    _description = 'Payment Mode Type'

    name = fields.Char('Name', size=64, required=True, help='Payment Type')
    code = fields.Char('Code', size=64, required=True,
                       help='Specify the Code for Payment Type')
    ir_model_id = fields.Many2one(
        'ir.model', string='Payment wizard',
        help='Select the Payment Wizard for payments of this type. Leave '
             'empty for manual processing',
        domain=[('osv_memory', '=', True)])
    payment_order_type = fields.Selection(
        [('payment', 'Payment'),
         ('debit', 'Debit')],
        string='Order type', required=True, default='payment',
        help="This field determines if this type applies to customers "
             "(Debit) or suppliers (Payment)")
    active = fields.Boolean(string='Active', default=True)

    def _auto_init(self, cr, context=None):
        res = super(PaymentModeType, self)._auto_init(cr, context=context)
        # migrate xmlid from manual_bank_transfer to avoid dependency on
        # account_banking
        cr.execute(
            """UPDATE ir_model_data
            SET module='account_payment_order'
            WHERE module='account_banking' AND
            name='manual_bank_tranfer' AND
            model='payment.mode.type'""")
        return res
