import logging
import json

from odoo import http, _
from odoo.http import request, Response
from odoo.exceptions import UserError

from odoo.addons.payment_slimpay.models import slimpay_utils


_logger = logging.getLogger(__name__)


class SlimpayController(http.Controller):

    def _approval_url(self, so, acquirer_id, return_url):
        """ Helper to be used with website_sale to get a Slimpay URL for the
        end-user to sign a mandate and create a first payment online."
        """
        acquirer = request.env['payment.acquirer'].sudo().browse(acquirer_id)
        locale = request.env.context.get('lang', 'fr_FR').split('_')[0]
        # May emit a direct debit only if a mandate exists; unsupported for now
        subscriber = slimpay_utils.subscriber_from_partner(so.partner_id)
        return acquirer.slimpay_client.approval_url(
            so.payment_tx_id.reference, so.id, locale, so.amount_total,
            so.currency_id.name, so.currency_id.decimal_places,
            subscriber, return_url)

    @http.route(['/payment/slimpay/s2s/feedback'], type='http',
                auth='public', methods=['POST'], csrf=False)
    def feedback(self):
        """Controller called by slimpay once the customer has finished the
        checkout process. Performs basic checks then delegates to the acquirer.
        """
        post = json.loads(request.httprequest.data)
        _logger.debug('slimpay feedback, post=%s', post)
        tx_ref = post['reference']
        tx = request.env['payment.transaction'].sudo().search(
            [('reference', '=', tx_ref)])
        if len(tx) != 1:
            _logger.warning('Enable to find 1 transaction for %r', tx_ref)
            return Response('Incorrect transaction reference', status=200)
        if tx.acquirer_id.provider != 'slimpay':
            _logger.warning('Feedback called with non slimpay tx %r', tx_ref)
            return Response('Incorrect transaction handler', status=200)
        if tx.state == 'done':
            _logger.debug('Transaction %r is already completed!', tx_ref)
            return Response("OK", status=200)
        if not tx.acquirer_id._slimpay_s2s_validate(tx, post):
            _logger.warning('Invalid feedback for transaction %r', tx_ref)
            return Response('Invalid feedback for order', status=200)
        return Response("OK", status=200)
