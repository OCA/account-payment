import logging

from iso8601 import parse_date

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

from slimpay_utils import SlimpayClient


_logger = logging.getLogger(__name__)


def _signed_date(mandate):
    return parse_date(mandate['dateSigned'])


class PaymentAcquirerSlimpay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('slimpay', 'Slimpay')])
    slimpay_api_url = fields.Char(
        'API base url',
        required_if_provider='slimpay',
        groups='base.group_user')
    slimpay_creditor = fields.Char(
        'Creditor reference',
        size=64,
        required_if_provider='slimpay',
        groups='base.group_user')
    slimpay_app_id = fields.Char(
        'OAuth application Id',
        size=64,
        required_if_provider='slimpay',
        groups='base.group_user')
    slimpay_app_secret = fields.Char(
        'OAuth application Secret',
        size=64,
        required_if_provider='slimpay',
        groups='base.group_user')

    @property
    def slimpay_client(self):
        if not hasattr(self, '_slimpay_client'):
            self._slimpay_client = SlimpayClient(
                self.slimpay_api_url, self.slimpay_creditor,
                self.slimpay_app_id, self.slimpay_app_secret)
        return self._slimpay_client

    def _slimpay_s2s_validate(self, sale_order, posted_data):
        """The posted data is validated using a http request to slimpay's
        server (to ensure posted data has not been forged), then the
        transaction status is updated.
        """
        sale_order.ensure_one()
        assert sale_order.payment_acquirer_id.provider == 'slimpay'
        so_url = posted_data['_links']['self']['href']
        doc = self.slimpay_client.get(so_url)
        _logger.info("Slimpay corresponding order doc: %s", doc)
        assert doc['reference'] == str(sale_order.id)
        slimpay_state = doc['state']
        tx = sale_order.payment_tx_id
        tx_attrs = {
            'acquirer_reference': doc['id'],
        }
        if slimpay_state == 'closed.completed':
            self._slimpay_tx_completed(tx, doc, **tx_attrs)
            return True
        elif slimpay_state.startswith("closed.aborted"):
            tx_attrs['state'] = 'cancel'
        tx.write(tx_attrs)
        # Confirm sale if necessary
        tx._confirm_so(acquirer_name='slimpay')
        return False

    def _slimpay_tx_completed(self, tx, order_doc, **tx_attrs):
        tx_attrs['state'] = 'done'
        tx_attrs['date_validate'] = parse_date(order_doc['dateClosed'])
        tx.write(tx_attrs)
        if tx.sudo().callback_eval:
            safe_eval(tx.sudo().callback_eval, {'self': self})
        # Confirm sale if necessary
        tx._confirm_so(acquirer_name='slimpay')
        # Use mandate as a token for later automatic payments
        partner = tx.sale_order_id.partner_id
        client = self.slimpay_client
        mandate_doc = client.get_from_doc(order_doc, 'get-mandate')
        mandate_id = mandate_doc['id']
        bank_account_doc = client.get_from_doc(mandate_doc, 'get-bank-account')
        token_name = u'IBAN %s (%s)' % (
            bank_account_doc['iban'], bank_account_doc['institutionName'])
        token = self.env['payment.token'].create({
            'name': token_name,
            'partner_id': partner.id,
            'acquirer_id': tx.acquirer_id.id,
            'acquirer_ref': mandate_id,
        })
        token.payment_ids |= tx
        partner.payment_token_id = token.id
        _logger.info('Added token id %s for %s', token.id, token.name)


class SlimpayTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.multi
    def slimpay_s2s_do_transaction(self, **kwargs):
        """ Perform a payment through a server to server call using a previously
        signed mandate.
        """
        # See contract_payment_auto/models/account_analytic_account.py:99
        self.acquirer_id.slimpay_client.create_payin(
            'TR%d' % self.id, self.payment_token_id.acquirer_ref,
            self.amount, self.currency_id.name)
