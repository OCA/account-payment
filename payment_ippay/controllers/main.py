"""Ippay payment controller."""

from werkzeug.urls import url_encode
from odoo import http, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.addons.account_payment.controllers.payment import PaymentPortal
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.http import request


class PaymentPortal(PaymentPortal):
    """Ippay payment portal."""

    @http.route(
        "/invoice/pay/<int:invoice_id>/s2s_token_tx",
        type="http",
        auth="public",
        website=True,
    )
    def invoice_pay_token(self, invoice_id, pm_id=None, **kwargs):
        """Use a token to perform a s2s transaction."""
        if not kwargs.get('acquirer_id'):
            kwargs = kwargs['kwargs']
        if kwargs.get('ippay_acquirer'):
            acquirer = request.env['payment.acquirer'].browse(
                int(kwargs.get('ippay_acquirer')))
            if acquirer.provider == 'ippay':

                error_url = kwargs.get('error_url', '/my')
                access_token = kwargs.get('access_token')
                params = {}
                if access_token:
                    params['access_token'] = access_token

                invoice_sudo = request.env['account.invoice'].sudo().browse(
                    invoice_id).exists()

                if not invoice_sudo:
                    params['error'] = 'pay_invoice_invalid_doc'
                    return request.redirect(_build_url_w_params(
                        error_url, params))

                success_url = kwargs.get(
                    'success_url', "%s?%s" % (
                        invoice_sudo.access_url,
                        url_encode({'access_token': access_token})
                        if access_token else '')
                )
                try:
                    token = request.env['payment.token'].sudo().browse(
                        int(pm_id))
                except (ValueError, TypeError):
                    token = False
                # Updated the Partner refrence for ippay payment
                token_owner = invoice_sudo.partner_id
                if not token or token.partner_id != token_owner:
                    params['error'] = 'pay_invoice_invalid_token'
                    return request.redirect(_build_url_w_params(
                        error_url, params))

                vals = {
                    'payment_token_id': token.id,
                    'type': 'server2server',
                    'return_url': _build_url_w_params(success_url, params),
                }
                tx = invoice_sudo._create_payment_transaction(vals)
                tx._ippay_s2s_do_payment(invoice_sudo)
                PaymentProcessing.add_payment_transaction(tx)

                params['success'] = 'pay_invoice'
                return request.redirect('/payment/process')

        return super(PaymentPortal, self).invoice_pay_token(
            invoice_id=invoice_id, pm_id=pm_id, kwargs=kwargs)

    @http.route(
        ["/payment/ippay/s2s/create_json_3ds"],
        type="json", auth="public", csrf=False
    )
    def ippay_s2s_create_json_3ds(self, verify_validity=False, **kwargs):
        """Create Payment Transaction."""
        token = False
        acquirer = request.env["payment.acquirer"].browse(
            int(kwargs.get("acquirer_id"))
        )
        try:
            kwargs = dict(kwargs, partner_id=kwargs.get("partner"))
            token = acquirer.s2s_process(kwargs)
        except ValidationError as e:
            message = e.args[0]
            if isinstance(message, dict) and "missing_fields" in message:
                if request.env.user._is_public():
                    message = _("Please sign in to complete the payment.")
                    # update message if portal mode = b2b
                    if (request.env["ir.config_parameter"].sudo().get_param(
                            "auth_signup.allow_uninvited", "False").lower() == "false"):
                        message += _(
                            " If you don't have any account, ask your"
                            " salesperson to grant you a portal access. "
                        )
                else:
                    msg = _(
                        "The transaction cannot be processed because some "
                        "contact details are missing or invalid: "
                    )
                    message = msg + ", ".join(message["missing_fields"]) + ". "
                    message += _("Please complete your profile. ")

            return {"error": message}
        except UserError as e:
            return {
                "error": e.name,
            }

        if not token:
            return {"result": False}

        return {
            "result": True,
            "id": token.id,
            "short_name": token.short_name,
            "3d_secure": False,
            "verified": True,
        }
