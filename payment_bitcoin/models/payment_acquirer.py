import logging
import pprint  # from odoo import models, fields, api

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class BitcoinPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('bitcoin', 'Bitcoin')])

    @api.multi
    def bitcoin_form_generate_values(self, values):
        values.update({'return_url': '/shop/payment/validate'})
        return values

    @api.multi
    def bitcoin_get_form_action_url(self):
        return '/payment/bitcoin/feedback'


class BitcoinPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def create(self, values):
        values['date'] = fields.Datetime.now()
        if values.get('acquirer_id'):
            acquirer = self.env['payment.acquirer'].browse(
                values['acquirer_id'])
            if acquirer.provider == 'bitcoin':
                order_ref = values.get('reference')
                sale_order_ids = values.get('sale_order_ids',[])
                if sale_order_ids:
                    resp = self.env['bitcoin.rate'].get_rate(order_id=sale_order_ids[0][2][0])
                    if resp:
                        values['bitcoin_address'] = resp[0]
                        values['bitcoin_amount'] = resp[1]
                        values['bitcoin_unit'] = resp[2]
        return super(BitcoinPaymentTransaction, self).create(values)

    @api.model
    def _bitcoin_form_get_tx_from_data(self, data):
        reference = data.get('reference')
        txs = self.search([('reference', '=', reference)])

        if not txs or len(txs) > 1:
            error_msg = 'received data for reference %s' % (
                pprint.pformat(reference))
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        return txs

    @api.multi
    def _bitcoin_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        # reference = data['reference']
        # if reference != self.reference:
        #     invalid_parameters.append(
        #         ('Reference', reference, self.reference))
        if float_compare(float(data.get('amount', '0.0')), self.amount, 2):
            invalid_parameters.append(
                ('amount', data.get('amount'), '%.2f' % self.amount))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(
                ('currency', data.get('currency'), self.currency_id.name))
        return invalid_parameters

    @api.multi
    def _bitcoin_form_validate(self, data):
        _logger.info(
            'Validated . payment for tx %s: set as pending' % self.reference)
        self._set_transaction_pending()
        return self.write({'state': 'pending'})
