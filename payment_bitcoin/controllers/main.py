# -*- coding: utf-8 -*-
# © ZedeS Technologies, initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request
from openerp.tools.translate import _

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
            'Beginning form_feedback with post data %s' % (post))
        request.registry['payment.transaction'].\
            form_feedback(cr, uid, post, 'bitcoin', context)
        return werkzeug.utils.redirect(post.pop('return_url', '/'))

    @http.route(['/payment_bitcoin/rate'],
                type='json',
                auth="none")
    def payment_bitcoin_rate(self, order_id=False, order_ref=False):
        cr, registry = request.cr, request.registry
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

        cr, context = request.cr, request.context
        order = request.registry['sale.order'].\
            browse(cr, SUPERUSER_ID, sale_order_id, context=context)

        if order.payment_acquirer_id.provider == 'bitcoin':
            bitcoin_address = order.payment_tx_id.bitcoin_address
            bitcoin_amount = order.payment_tx_id.bitcoin_amount

            msg = _("Please send %s mBTC to the following address: %s")\
                  % (bitcoin_amount, bitcoin_address)
            resp['message'] += msg
        return resp

    @http.route(['/shop/payment'], type='http',
                auth="public", website=True)
    def payment(self, **post):
        context = request.context
        order = request.website.sale_get_order(context=context)
        request.context.update({
            'order_id': order.id,
            'order_ref': order.name
        })
        return super(website_sale, self).payment(**post)
