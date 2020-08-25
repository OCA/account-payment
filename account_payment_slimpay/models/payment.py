import logging

from iso8601 import parse_date

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval

from .slimpay_utils import SlimpayClient


_logger = logging.getLogger(__name__)


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

    def _slimpay_s2s_validate(self, tx, posted_data):
        """The posted data is validated using a http request to slimpay's
        server (to make sure posted data has not been forged), then the
        transaction status is updated.
        """
        url = posted_data['_links']['self']['href']
        doc = self.slimpay_client.get(url)
        _logger.info("Slimpay corresponding order doc: %s", doc)
        assert doc['reference'] == tx.reference
        slimpay_state = doc['state']
        tx_attrs = {
            'acquirer_reference': doc['id'],
        }
        if slimpay_state == 'closed.completed':
            self._slimpay_tx_completed(tx, doc, **tx_attrs)
            return True
        elif slimpay_state.startswith("closed.aborted"):
            tx._set_transaction_cancel()
        else:
            tx._set_transaction_pending()
        tx.write(tx_attrs)
        return False

    def _slimpay_tx_completed(self, tx, order_doc, **tx_attrs):
        _logger.info('Trying to complete transaction id %s', tx.id)
        tx.write(tx_attrs)
        # Confirm sale if necessary
        _logger.info('Setting sale transaction as done...')
        tx._set_transaction_done()
        tx._post_process_after_done()
        # Use mandate as a token for later automatic payments
        partner = tx.partner_id
        client = self.slimpay_client
        _logger.info("Fetching new partner's mandate...")
        mandate_doc = client.get_from_doc(order_doc, 'get-mandate')
        mandate_id = mandate_doc['id']
        bank_account_doc = client.get_from_doc(mandate_doc, 'get-bank-account')
        token_name = 'IBAN %s (%s)' % (
            bank_account_doc['iban'], bank_account_doc['institutionName'])
        token = self.env['payment.token'].create({
            'name': token_name,
            'partner_id': partner.id,
            'acquirer_id': tx.acquirer_id.id,
            'acquirer_ref': mandate_id,
        })
        token.payment_ids |= tx
        _logger.info('Added token id %s for %s', token.id, token.name)
        return token


class SlimpayTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.multi
    def slimpay_s2s_do_transaction(self, **kwargs):
        """ Perform a payment through a server to server call using a previously
        signed mandate.
        """
        _logger.debug('Starting auto Slimpay Transaction TR%s...', self.id)
        client = self.acquirer_id.slimpay_client
        mandate_ref = client.action('GET', 'get-mandates', params={
            'id': self.payment_token_id.acquirer_ref})['reference']
        _logger.debug('Found mandate reference: %s', mandate_ref)
        label = self.env.context.get(
            'slimpay_payin_label', self.reference or 'TR%d' % self.id)
        result, acquirer_reference = client.create_payin(
            mandate_ref, self.amount, self.currency_id.name,
            self.currency_id.decimal_places, label)
        _logger.debug('Payin creation result: %s, reference: %s',
                      result, acquirer_reference)
        self.update({'state': 'done' if result else 'error',
                     'acquirer_reference': acquirer_reference})
        return result
