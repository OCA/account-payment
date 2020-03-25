import logging
import pprint

import werkzeug

import odoo.addons.website_sale.controllers.main
from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BitcoinController(http.Controller):
    _accept_url = '/payment/bitcoin/feedback'

    @http.route(
        ['/payment/bitcoin/feedback'], type='http', auth='none', csrf=False)
    def transfer_form_feedback(self, **post):
        _logger.debug(
            'Beginning form_feedback with post data %s', pprint.pformat(post))
        request.env['payment.transaction'].sudo().form_feedback(
            post, 'bitcoin')
        return werkzeug.utils.redirect(post.pop('return_url', '/'))

    @http.route(['/payment_bitcoin/rate'], type='json', auth="none")
    def payment_bitcoin_rate(self, order_id=False, order_ref=False):
        _logger.debug(
            'bitcoin rate lookup for Order ID %s, Order Ref %s' % (
                order_id, order_ref))
        return request.env['bitcoin.rate'].sudo().get_rate(order_id, order_ref)

    @http.route(
        ['/report/barcode/bitcoin',
         '/report/barcode/bitcoin/<type>/<path:value>'],
        type='http', auth="public")
    def report_barcode_bitcoin(self, type, value, width=600, height=100,
                               humanreadable=0):
        """Contoller able to render barcode images thanks to reportlab.
        Samples:
          <img t-att-src="'/report/barcode/QR/%s' % o.name"/>
          <img t-att-src="'/report/barcode/?type=%s&amp;value=%s&amp;
            width=%s&amp;height=%s' % ('QR', o.name, 200, 200)"/>

        :param type: Accepted types: 'Codabar', 'Code11', 'Code128',
        'EAN13', 'EAN8', 'Extended39', 'Extended93', 'FIM', 'I2of5', 'MSI',
        'POSTNET', 'QR', 'Standard39', 'Standard93', 'UPCA', 'USPS_4State'
        :param humanreadable: Accepted values: 0 (default) or 1.
        1 will insert the readable value
        at the bottom of the output image
        """
        try:
            value = value.replace("$$", "?")
            value = value.replace("*$", "&")
            barcode = request.env['ir.actions.report'].barcode(
                type, value, width=width, height=height,
                humanreadable=humanreadable)
        except (ValueError, AttributeError):
            raise werkzeug.exceptions.HTTPException(
                description='Cannot convert into barcode.')

        return request.make_response(
            barcode, headers=[('Content-Type', 'image/png')])


class WebsiteSale(odoo.addons.website_sale.controllers.main.WebsiteSale):

    @http.route(
        '/shop/payment/get_status/<int:sale_order_id>', type='json',
        auth="public", website=True)
    def payment_get_status(self, sale_order_id, **post):
        resp = super(WebsiteSale, self).payment_get_status(sale_order_id)
        order = request.env['sale.order'].sudo().browse(sale_order_id)
        if order.payment_acquirer_id.provider == 'bitcoin':
            after_panel_heading = resp['message'].find(
                b'</div>', resp['message'].find(
                    b'<div class="panel-heading">'))

            if order.payment_tx_id.bitcoin_unit == 'mBTC':
                bitcoin_amount = order.payment_tx_id.bitcoin_amount / 1000.0
            else:
                bitcoin_amount = order.payment_tx_id.bitcoin_amount

            uri = _('bitcoin:%s$$amount=%s*$message=%s') % (
                order.payment_tx_id.bitcoin_address, bitcoin_amount,
                order.name)

            info = _("Please send %s %s to the following address: %s") % (
                order.payment_tx_id.bitcoin_amount,
                order.payment_tx_id.bitcoin_unit,
                order.payment_tx_id.bitcoin_address)

            if after_panel_heading:
                after_panel_heading += 6
                msg = (
                    b'<div class="panel-body" style="padding-bottom:0px;">'
                    b'<h4><strong>%s</strong></h4>'
                    b'</div>'
                    b'<div class="panel-body" style="padding-top:5px; '
                    b'padding-bottom:0px;">'
                    b'<center><img src="/report/barcode/bitcoin/?type=QR&amp;'
                    b'value=%s&amp;width=300&amp;height=300"></center>'
                    b'</div>'
                ) % (info.encode(), uri.encode())

                resp['message'] = resp['message'][:after_panel_heading] +\
                    msg + resp['message'][after_panel_heading:]
            else:
                resp['message'] += info.encode()
                resp['message'] += (
                    b'<center>'
                    b'<img src="/report/barcode/bitcoin/?type=QR&amp;'
                    b'value=%s&amp;width=300&amp;height=300"></center>'
                ) % uri.encode()
            resp['recall'] = False
        return resp
