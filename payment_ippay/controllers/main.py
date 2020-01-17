"""Ippay Cotroller."""
# See LICENSE file for full copyright and licensing details.

import logging
import pprint
import werkzeug
import requests
from werkzeug import urls, utils

try:
    # For Python 3.0 and later
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
except ImportError:
    # For Python 2's urllib2
    from urllib2 import urlopen, Request
    from urllib import urlencode

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

error_str = ''


class IppayController(http.Controller):
    """Ipapay Controller."""

    # _notify_url = '/payment/ippay/ipn/'
    # _cancel_url = '/payment/ippay/cancel/'

    # def _encode_arguments(self, params):
    #     """UTF-8 encode the argument values - used primarily """
    #     return dict([k, v] for k, v in params.items())

    # def parse(self, raw_response):
    #     """Parse a HTTP response"""
    #     # Read through each line....
    #     self._args = {}
    #     for line in str(raw_response).split('\r\n'):
    #         # Check it isn't 'empty'
    #         if line.strip():
    #             try:
    #                 name, value = line.split('=', 1)
    #             except Exception:
    #                 raise RuntimeError(u'Malformed response! Line "%s"' % line)
    #             else:
    #                 self._args[name.strip()] = value.strip()
    #     return self._args

    # @http.route('/ippay', type='http', auth="public", csrf=False,
    #             website=True)
    # def payment_ippay(self, transaction_id=None, **post):
    #     """Request send for payment."""
    #     print ("\n\n\n\n >>>>>>>>> payment_ippaypayment_ippaypayment_ippay", post)
    #     return request.render(
    #         'payment_ippay.website_ippay_form', post)
        # if post:
        #     tran_obj = request.env['payment.transaction']
        #     if not transaction_id:
        #         try:
        #             tx = request.website.sudo().sale_get_transaction()
        #         except:
        #             tx = tran_obj.search(
        #                 [('sale_order_ids', '=',
        #                   request.session.get('sale_last_order_id'))], limit=1)
        #     else:
        #         tx = tran_obj.sudo().browse(transaction_id)
        #     data = urlencode(self._encode_arguments(post))
        #     data = data.encode('ascii')
        #     ippay_urls = request.env['payment.acquirer'].\
        #         _get_ippay_urls(tx and tx.acquirer_id.environment or 'prod')
        #     validate_url = ippay_urls['ippay_form_url']
        #     url_request = Request(validate_url, data)
        #     try:
        #         response_page = urlopen(url_request)
        #     except Exception as e:
        #         raise UserError('Unable to contact "%s" because: %s' % (
        #             post.get('turl'), e))
        #     else:
        #         response = response_page.read()
        #         response = self.parse(response.decode("utf-8"))
        #     if response and response.get('Status') in ["OK", "OK REPEATED"]:
        #         tx.write({
        #             'SecurityKey': response.get('SecurityKey'),
        #             'statusdetail': response.get('StatusDetail'),
        #             'VPSTxId': response.get('VPSTxId'),
        #             'tran_res': response
        #         })
        #         next_url = response.get('NextURL')
        #         return http.local_redirect(next_url)
        #     else:
        #         error = str(response.get('StatusDetail').replace(':', ''))
        #         error_val = {
        #             'error': error
        #         }
        #         return request.render('payment_ippay.Failed', error_val)

    # def ippay_validate_data(self, **post):
    #     """Ippay DPN."""
    #     for item in request.website.sale_get_order().order_line:
    #         item.qty_delivered = item.product_uom_qty
    #     res = request.env['payment.transaction'
    #                       ].sudo().form_feedback(post, 'ippay')
    #     return res

    # @http.route('/payment/ippay/cancel', type='http', auth="public",
    #             csrf=False, website=True)
    # def ippay_cancel(self, **post):
    #     """When the user cancels its ippay payment: GET on this route."""
    #     _logger.info('''Ippay : entering form_feedback cancel with post
    #         data %s''', pprint.pformat(post))
    #     kwargs = {
    #         'error': error_str,
    #     }
    #     return request.render("payment_ippay.Failed", kwargs)

    # @http.route('/payment/ippay/ipn/', type='http', auth='none',
    #             methods=['POST'], csrf=False, website=True)
    # def ippay_ipn(self, **post):
    #     """Ippay IPN."""
    #     _logger.info('Ippay : entering form_feedback with post data %s',
    #                  pprint.pformat(post))
    #     base_url = request.env['ir.config_parameter'
    #                            ].sudo().get_param('web.base.url')
    #     if post and post.get('Status') in ['OK']:
    #         self.ippay_validate_data(**post)
    #         # please do not change with pep8 standards next line
    #         template = """Status=""" + post.get('Status') + """\r\nRedirectURL=""" + base_url + """/payment/process"""
    #     else:
    #         global error_str
    #         error_str = post.get('StatusDetail')
    #         # please do not change with pep8 standards next line
    #         template = """Status=""" + post.get('Status') + """\r\nRedirectURL=""" + base_url + """/payment/ippay/cancel"""
    #     return template

    # @http.route('/payment/ippay/charge', type='http', auth="public",
    #             website=True)
    # def payment(self, **kwargs):
    #     """Payment Request."""
    #     print("kwargs", kwargs)
    #     transaction_obj = request.env['payment.transaction']
    #     tx = None
    #     if kwargs.get('tx_ref'):
    #         tx = transaction_obj.sudo().search([(
    #             'reference', '=', kwargs['tx_ref'])])
    #     if not tx:
    #         tx_id = (request.session.get('sale_transaction_id') or
    #                  request.session.get('website_payment_tx_id'))
    #         tx = transaction_obj.sudo().browse(int(tx_id))
    #         if not tx:
    #             raise werkzeug.exceptions.NotFound()
    #     url = kwargs.get('tx_url')
    #     data = {
    #         'amount': str(int(float(kwargs.get('amount')) * 100)),
    #         'currency': kwargs.get('currency'),
    #         'description': 'Description',
    #         'email': kwargs.get('email') or '',
    #         'card[number]': kwargs.get('card-number'),
    #         'card[expiry_month]': kwargs.get('exp-month'),
    #         'card[expiry_year]': kwargs.get('exp-year'),
    #         'card[cvc]': kwargs.get('cvc'),
    #         'card[name]': kwargs.get('card-holder-name'),
    #         'card[address_line1]': kwargs.get('address1'),
    #         'card[address_line2]': '',
    #         'card[address_city]': kwargs.get('city'),
    #         'card[address_postcode]': kwargs.get('postcode'),
    #         'card[address_state]': kwargs.get('state'),
    #         'card[address_country]': kwargs.get('country'),
    #         'metadata[OrderNumber]': kwargs.get('order'),
    #         'metadata[CustomerName]': kwargs.get('customerName')
    #     }
    #     response = requests.post(
    #         url,
    #         data=data,
    #         auth=(kwargs.get("secret_key"), '')
    #     )

    #     response_json = response.json()
    #     if response_json.get('response') and\
    #             response_json.get('response'
    #                               ).get('status_message') == 'Success':
    #         for item in request.website.sale_get_order().order_line:
    #             item.qty_delivered = item.product_uom_qty
    #         _logger.info(
    #             'IppayPayments : entering form_feedback with post data %s',
    #             pprint.pformat(response_json)
    #         )
    #         request.env['payment.transaction'].sudo().with_context(
    #             lang=None).form_feedback(response_json, 'Ippaypayments')
    #         return http.local_redirect('/payment/process')
    #     else:
    #         if response_json.get('messages') and\
    #                 response_json.get('messages')[0].get('message'):
    #             error = response_json.get('messages')[0].get('message')
    #         else:
    #             error = response_json.get('error_description')
    #         _logger.info(error)
    #         kwargs = {
    #             'error': error or '',
    #         }
    #         return request.render("ippay_payment.failed", kwargs)

    @http.route(['/payment/ippay/s2s/create_json_3ds'], type='json', auth='public', csrf=False)
    def ippay_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        print ("\n\n\n\n>>>>>ippay_s2s_create", kwargs)
        token = False
        acquirer = request.env['payment.acquirer'].browse(int(kwargs.get('acquirer_id')))

        try:
            if not kwargs.get('partner_id'):
                kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
            token = acquirer.s2s_process(kwargs)
        except ValidationError as e:
            message = e.args[0]
            if isinstance(message, dict) and 'missing_fields' in message:
                if request.env.user._is_public():
                    message = _("Please sign in to complete the payment.")
                    # update message if portal mode = b2b
                    if request.env['ir.config_parameter'].sudo().get_param('auth_signup.allow_uninvited', 'False').lower() == 'false':
                        message += _(" If you don't have any account, ask your salesperson to grant you a portal access. ")
                else:
                    msg = _("The transaction cannot be processed because some contact details are missing or invalid: ")
                    message = msg + ', '.join(message['missing_fields']) + '. '
                    message += _("Please complete your profile. ")

            return {
                'error': message
            }
        except UserError as e:
            return {
                'error': e.name,
            }

        if not token:
            res = {
                'result': False,
            }
            return res

        res = {
            'result': True,
            'id': token.id,
            'short_name': token.short_name,
            '3d_secure': False,
            'verified': True, #Authorize.net does a transaction type of Authorization Only
                              #As Authorize.net already verify this card, we do not verify this card again.
        }
        #token.validate() don't work with Authorize.net.
        #Payments made via Authorize.net are settled and allowed to be refunded only on the next day.
        #https://account.authorize.net/help/Miscellaneous/FAQ/Frequently_Asked_Questions.htm#Refund
        #<quote>The original transaction that you wish to refund must have a status of Settled Successfully.
        #You cannot issue refunds against unsettled, voided, declined or errored transactions.</quote>
        print ("RESSSSSSSSSS", res)
        return res

    @http.route(['/payment/ippay/s2s/create'], type='http', auth='public')
    def ippay_s2s_create(self, **post):
        print ("\n\n\nippay_s2s_createippay_s2s_createippay_s2s_create", post)
        acquirer_id = int(post.get('acquirer_id'))
        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        acquirer.s2s_process(post)
        return utils.redirect("/payment/process")
