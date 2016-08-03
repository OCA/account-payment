# -*- coding: utf-8 -*-
# © initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint
import werkzeug
import openerp

from openerp import http, SUPERUSER_ID
from openerp.http import request

import openerp.addons.website_sale.controllers.main

_logger = logging.getLogger(__name__)


class BitcoinController(http.Controller):
    _accept_url = '/payment/bitcoin/feedback'

    @http.route(['/payment/bitcoin/feedback', ],
                type='http',
                auth='none')
    def transfer_form_feedback(self, **post):
        cr, uid, context = request.cr, SUPERUSER_ID, request.context
        _logger.info(
            'Beginning form_feedback with post data %s',
            pprint.pformat(post))  # debug
        request.registry['payment.transaction'].\
            form_feedback(cr, uid, post, 'bitcoin', context)
        return werkzeug.utils.redirect(post.pop('return_url', '/'))

    @http.route(['/payment_bitcoin/rate'],
                type='json',
                auth="none")
    def payment_bitcoin_rate(self, order_id=False, order_ref=False):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        b_vals = registry.get('bitcoin.rate').\
            get_rate(cr, SUPERUSER_ID, order_id, order_ref)
        return b_vals


class website_sale(openerp.addons.website_sale.controllers.main.website_sale):

    @http.route('/shop/payment/get_status/<int:sale_order_id>',
                type='json',
                auth="public",
                website=True)
    def payment_get_status(self, sale_order_id, **post):
        resp = super(website_sale, self).payment_get_status(sale_order_id)

        cr, uid, context = request.cr, request.uid, request.context
        order = request.registry['sale.order'].\
            browse(cr, SUPERUSER_ID, sale_order_id, context=context)

        if order.payment_acquirer_id.provider == 'bitcoin':
            bitcoin_address = order.payment_tx_id.bitcoin_address
            bitcoin_amount = order.payment_tx_id.bitcoin_amount

            msg = "Please send %s mBTC to the following address: %s"\
                  % (bitcoin_amount, bitcoin_address)
            resp['message'] += '<br/><br/>' + msg
        return resp
