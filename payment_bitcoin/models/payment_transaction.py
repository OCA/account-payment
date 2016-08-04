# -*- coding: utf-8 -*-
# © initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, api
from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.tools.float_utils import float_compare
import logging
_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def create(self, vals):
        if vals.get('acquirer_id'):
            acquirer = self.env['payment.acquirer'].\
                browse(vals['acquirer_id'])
            if acquirer.provider == 'bitcoin':
                order_ref = vals.get('reference')
                resp = self.env['bitcoin.rate'].get_rate(order_ref=order_ref)
                if resp:
                    vals['bitcoin_address'] = resp[0]
                    vals['bitcoin_amount'] = resp[1]
        return super(PaymentTransaction, self).create(vals)

    @api.cr_uid_ids_context
    def _bitcoin_form_get_tx_from_data(self, cr, uid, data, context=None):
        reference, amount, currency_name = \
            data.get('reference'),\
            data.get('amount'),\
            data.get('currency_name')
        tx_ids = self.search(
            cr, uid, [
                ('reference', '=', reference),
            ], context=context)

        if not tx_ids or len(tx_ids) > 1:
            error_msg = 'received data for reference %s' % (reference)
            if not tx_ids:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        return self.browse(cr, uid, tx_ids[0], context=context)

    @api.cr_uid_ids_context
    def _bitcoin_form_get_invalid_parameters(
            self, cr, uid, tx, data, context=None):
        invalid_parameters = []

        if float_compare(float(data.get('amount', '0.0')),
                         tx.amount, 2) != 0:
            invalid_parameters.append(('amount',
                                       data.get('amount'),
                                       '%.2f' % tx.amount))
        if data.get('currency') != tx.currency_id.name:
            invalid_parameters.append(('currency',
                                       data.get('currency'),
                                       tx.currency_id.name))

    @api.cr_uid_ids_context
    def _bitcoin_form_validate(self, cr, uid, tx, data, context=None):
        _logger.info('Validated . payment for tx %s: set as pending'
                     % (tx.reference))
        return tx.write({'state': 'pending'})

    bitcoin_address = fields.Char('Bitcoin Address')
    bitcoin_amount = fields.Float('Bitcoin Amount')
