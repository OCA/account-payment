# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import werkzeug
from openerp import http


class SisowController(http.Controller):
    _redirect_url = '/payment/sisow/redirect'
    _return_url = '/payment/sisow/return'

    @http.route(_redirect_url, type='http', auth='none')
    def redirect(self, issuerid=None):
        if not http.request.session.get('sale_transaction_id'):
            raise werkzeug.exceptions.NotFound()
        transaction = http.request.env['payment.transaction'].browse(
            http.request.session['sale_transaction_id'])
        if not transaction.acquirer_id.provider == 'sisow':
            raise werkzeug.exceptions.NotFound()
        if not http.request.session.get('sisow_issuer') and not issuerid:
            if 'referer' in http.request.httprequest.headers:
                return werkzeug.utils.redirect(
                    http.request.httprequest.headers['referer'])
            raise werkzeug.exceptions.NotFound()
        if transaction.state not in ['draft', 'pending']:
            raise werkzeug.exceptions.NotFound()
        redirect_url = transaction.acquirer_id._sisow_request_transaction(
            transaction, issuerid or http.request.session['sisow_issuer'],
            http.request.httprequest.url_root + self._return_url[1:],
        )
        return werkzeug.utils.redirect(redirect_url)

    @http.route('/payment/sisow/issuer/<issuerid>', type='json', auth='none')
    def issuer(self, issuerid):
        http.request.session['sisow_issuer'] = issuerid

    @http.route(_return_url, type='http', auth='none')
    def returnurl(self, **kwargs):
        if http.request.env['payment.transaction'].form_feedback(
            kwargs, 'sisow'
        ):
            return werkzeug.utils.redirect(
                kwargs.get('return_url', '/shop/payment/validate')
            )
        else:
            raise werkzeug.exceptions.NotFound()
