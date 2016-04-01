# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# import time
from openerp import models, fields, api, SUPERUSER_ID


class PaymentMode(models.Model):
    _name = 'payment.mode'
    _description = 'Payment Mode'

    name = fields.Char('Name', required=True, help='Mode of Payment')

    bank_id = fields.Many2one('res.partner.bank', "Bank account",
                              required=True,
                              help='Bank Account for the Payment Mode')

    journal_id = fields.Many2one('account.journal', 'Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))],
                                 help='Bank or Cash Journal for the '
                                 'Payment Mode',oldname='journal')

    company_id = fields.\
        Many2one('res.company', 'Company', required=True,
                 default=lambda self: self.env.user.company_id.id)

    partner_id = fields.Many2one('res.partner',
                                 related='company_id.partner_id',
                                 string='Partner', store=True)


    def _get_manual_bank_transfer(self, cr, uid, context=None):
        """ hack: pre-create the manual bank transfer that is also
        defined in the data directory, so we have an id in to use
        in _auto_init """
        model_data = self.pool['ir.model.data']
        try:
            _, res = model_data.get_object_reference(
                cr, uid,
                'account_payment_order',
                'manual_bank_tranfer')
        except ValueError:
            payment_mode_type = self.pool['payment.mode.type']
            res = payment_mode_type.create(
                cr, uid,
                {'name': 'Manual Bank Transfer',
                 'code': 'BANKMAN'})
            model_data.create(
                cr, uid,
                {'module': 'account_payment_order',
                 'model': 'payment.mode.type',
                 'name': 'manual_bank_tranfer',
                 'res_id': res,
                 'noupdate': False})
        return res

    def _auto_init(self, cr, context=None):
        """ hack: pre-create and initialize the type column so that the
        constraint setting will not fail, this is a hack, made necessary
        because Odoo tries to set the not-null constraint before
        applying default values """
        self._field_create(cr, context=context)
        column_data = self._select_column_data(cr)
        if 'type' not in column_data:
            default_type = self._get_manual_bank_transfer(
                cr, SUPERUSER_ID, context=context)
            if default_type:
                cr.execute('ALTER TABLE "{table}" ADD COLUMN "type" INTEGER'.
                           format(table=self._table))
                cr.execute('UPDATE "{table}" SET type=%s'.
                           format(table=self._table),
                           (default_type,))
        return super(PaymentMode, self)._auto_init(cr, context=context)

    @api.model
    def _default_type(self):
        return self.env.ref(
            'account_payment_order.'
            'manual_bank_tranfer', raise_if_not_found=False)\
            or self.env['payment.mode.type']

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
