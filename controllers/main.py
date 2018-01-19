import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SlimpayController(http.Controller):

    @http.route(['/payment/slimpay/create_sepa_direct_debit'],
                type='json', auth='public')
    def create_sepa_direct_debit(self, **post):
        _logger.warning('CREATE_SEPA_DIRECT_DEBIT CALLED! post: %s', post)
        # Get some required database objects
        so_id = request.session['sale_order_id']
        so = request.env['sale.order'].sudo().browse(so_id)
        partner = so.partner_id
        acquirer_id = int(post['acquirer'])
        acquirer = request.env['payment.acquirer'].sudo().browse(acquirer_id)
        mandate = acquirer.slimpay_get_valid_mandate(partner)
        return_url = post.pop('return_url', '/')
        if mandate is None:
            # If the partner has no valid mandate, ask a signature and pay:
            url = acquirer.slimpay_get_approval_url(so, partner, return_url)
            _logger.info('Approval URL: %s', url)
        else:
            # Otherwise only create a direct debit:
            url = return_url  # XXX
            raise Exception('Debit with pre-existing mandate not implemented!')
        return url

    def _create_transaction(self, sale_order):
        pass
