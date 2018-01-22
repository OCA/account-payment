import logging

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


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
        response = self.payment_transaction(
            acquirer_id, tx_type='form', token=None, **kwargs)
        _logger.debug('initial response:\n%s', response)
        # Get some required database objects
        so_id = request.session['sale_order_id']
        so = request.env['sale.order'].sudo().browse(so_id)
        partner = so.partner_id
        acquirer = request.env['payment.acquirer'].sudo().browse(acquirer_id)
        mandate = acquirer.slimpay_get_valid_mandate(partner)
        return_url = '/shop/payment/validate'
        if mandate is None:
            # If the partner has no valid mandate, ask a signature and pay:
            url = acquirer.slimpay_get_approval_url(so, partner, return_url)
        else:
            # Otherwise only create a direct debit:
            # raise Exception('Debit with pre-existing mandate unimplemented!')
            url = acquirer.slimpay_get_approval_url(so, partner, return_url)
        _logger.debug('Approval URL: %s', url)
        return url

    @http.route(['/payment/slimpay/s2s/feedback'], type='json',
                auth='public', methods=['POST'], csrf=False)
    def feedback(self):
        """Controller called by slimpay once the customer has finished the
        checkout process. Performs basic checks then delegates to the acquirer.
        """
        post = request.jsonrequest
        _logger.debug('slimpay feedback, post=%s', post)
        ref = post['reference']
        so = request.env['sale.order'].sudo().search([('name', '=', ref)])
        if len(so) != 1:
            _logger.warning('Enable to find 1 sale order for %r', ref)
            return
        if so.payment_acquirer_id.provider != 'slimpay':
            _logger.warning('Feedback called with non slimpay order %r', ref)
            return
        if not so.payment_acquirer_id._slimpay_s2s_validate(so, post):
            _logger.warning('Invalid feedback for order %r', ref)
            return
