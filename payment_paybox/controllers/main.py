# coding: utf-8
from openerp import http
import logging
import werkzeug.utils
import pprint
from openerp.http import request
from openerp import SUPERUSER_ID

logger = logging.getLogger(__name__)

class PayboxController(http.Controller):
    @http.route("/payment/paybox/ipn", auth='none')
    def ipn(self, **post):
        logger.info('paybox: entering ipn with post data %s', pprint.pformat(post))  # debug
        cr, uid, context = request.cr, SUPERUSER_ID, request.context
        request.registry['payment.transaction'].form_feedback(cr, uid, post, 'paybox', context=context)
        return ""

    @http.route([
        '/payment/paybox/accept', '/payment/paybox/test/accept',
        '/payment/paybox/decline', '/payment/paybox/test/decline',
        '/payment/paybox/cancel', '/payment/paybox/test/cancel',
    ], auth='none')
    def paybox_form_feedback(self, **post):
        """Paybox contacts using GET, at least for accept """
        logger.info('paybox: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        cr, uid, context = request.cr, SUPERUSER_ID, request.context
        request.registry['payment.transaction'].form_feedback(cr, uid, post, 'paybox', context=context)
        return werkzeug.utils.redirect(post.pop('return_url', '/shop/payment/validate'))
