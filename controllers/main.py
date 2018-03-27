import logging
import json

from coreapi.exceptions import ErrorMessage as CoreAPIErrorMessage

from odoo import http
from odoo.http import request, Response

from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo.addons.payment_slimpay.models import slimpay_utils


_logger = logging.getLogger(__name__)


class SlimpayController(WebsiteSale):

    @http.route(['/payment/slimpay_transaction/<int:acquirer_id>'],
                type='json', auth="public", website=True)
    def payment_slimpay_transaction(
            self, acquirer_id, tx_type='form', token=None, **kwargs):
        """ Slimpay specific payment transaction creation. Uses the standard
        website_sale method, but creates the slimpay order and respond with
        slimpay's redirect URL instead of a form to be submitted.
        """
        _logger.debug('payment_transaction CALLED! kwargs: %s', kwargs)
        _logger.debug('session data: %s', request.session)
        response = self.payment_transaction(
            acquirer_id, tx_type='form', token=None, **kwargs)
        _logger.debug('initial response:\n%s', response)
        # Get some required database objects
        so_id = request.session['sale_order_id']
        so = request.env['sale.order'].sudo().browse(so_id)
        ref, amount, currency = so.id, so.amount_total, so.currency_id
        partner = so.partner_id
        acquirer = request.env['payment.acquirer'].sudo().browse(acquirer_id)
        return_url = '/shop/payment/validate'
        locale = request.env.context.get('lang', 'fr_FR').split('_')[0]
        # May emit a direct debit only if a mandate exists; unsupported for now
        subscriber = slimpay_utils.subscriber_from_partner(partner)
        try:
            return acquirer.slimpay_client.approval_url(
                ref, locale, amount, currency, subscriber, return_url)
        except CoreAPIErrorMessage as exc:
            _logger.error('CoreAPIErrorMessage: %s', exc)
            if unicode(exc).startswith(u'Duplicate order'):
                _logger.warning('GOT DUPLICATE ORDER FOR %s', so.name)
                url = acquirer.slimpay_client.get_approval_url(so.id)
                if url:
                    return url
            raise Exception(exc.error['message'])

    @http.route(['/payment/slimpay/s2s/feedback'], type='http',
                auth='public', methods=['POST'], csrf=False)
    def feedback(self):
        """Controller called by slimpay once the customer has finished the
        checkout process. Performs basic checks then delegates to the acquirer.
        """
        post = json.loads(request.httprequest.data)
        _logger.debug('slimpay feedback, post=%s', post)
        ref = int(post['reference'])
        so = request.env['sale.order'].sudo().browse(ref)
        if len(so) != 1:
            _logger.warning('Enable to find 1 sale order for %r', ref)
            return Response('Incorrect sale order reference', status=500)
        if so.payment_acquirer_id.provider != 'slimpay':
            _logger.warning('Feedback called with non slimpay order %r', ref)
            return Response('Incorrect sale order handler', status=500)
        if not so.payment_acquirer_id._slimpay_s2s_validate(so, post):
            _logger.warning('Invalid feedback for order %r', ref)
            return Response('Invalid feedback for order', status=500)
        return Response("OK", status=200)

    def _get_mandatory_billing_fields(self):
        ''' Replace "name" by "firstname" and "lastname" '''
        fields = super(SlimpayController, self)._get_mandatory_billing_fields()
        return ['firstname', 'lastname'] + [f for f in fields if f != 'name']

    def _get_mandatory_shipping_fields(self):
        ''' Replace "name" by "firstname" and "lastname" '''
        fields = super(SlimpayController,
                       self)._get_mandatory_shipping_fields()
        return ['firstname', 'lastname'] + [f for f in fields if f != 'name']

    def values_postprocess(self, order, mode, values, errors, error_msg):
        """ Do not drop firstname and lastname fields for `partner_firstname`
        module compatiblity. """
        new_values, errors, error_msg = super(
            SlimpayController, self).values_postprocess(order, mode, values,
                                                        errors, error_msg)
        for field in ('firstname', 'lastname'):
            if field in values:
                _logger.debug(
                    "payment_slimpay postprocess: %s value has finally *not* "
                    "been dropped.", field)
                new_values[field] = values[field]
        return new_values, errors, error_msg
