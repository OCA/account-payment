import logging
import json

from odoo import http
from odoo.http import request, Response


_logger = logging.getLogger(__name__)


class SlimpayController(http.Controller):

    @http.route(['/payment/slimpay/s2s/feedback'], type='http',
                auth='public', methods=['POST'], csrf=False)
    def feedback(self):
        """Controller called by slimpay once the customer has finished the
        checkout process. Performs basic checks then delegates to the acquirer.
        """
        post = json.loads(request.httprequest.data.decode('utf-8'))
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
