# Copyright 2024 Alexandre D. Díaz - Grupo Isonor

import binascii

from odoo import SUPERUSER_ID, _, fields, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.portal.controllers.mail import _message_post_helper


class PortalAccountPaymentSign(PortalAccount):
    @http.route(
        ["/my/invoices/<int:invoice_id>/sign"], type="json", auth="public", website=True
    )
    def portal_invoice_sign(
        self, invoice_id, access_token=None, name=None, signature=None
    ):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get("access_token")
        try:
            inv_sudo = self._document_check_access(
                "account.move", invoice_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return {"error": _("Invalid invoice.")}

        if not inv_sudo.has_to_be_signed():
            return {
                "error": _(
                    "The invoice is not in a state requiring customer signature."
                )
            }
        if not signature:
            return {"error": _("Signature is missing.")}

        try:
            inv_sudo.write(
                {
                    "signed_by": name,
                    "signed_on": fields.Datetime.now(),
                    "signature": signature,
                }
            )
            request.env.cr.commit()
        except (TypeError, binascii.Error):
            return {"error": _("Invalid signature data.")}

        pdf = (
            request.env.ref("account.account_invoices")
            .with_user(SUPERUSER_ID)
            ._render_qweb_pdf([inv_sudo.id])[0]
        )

        _message_post_helper(
            "account.move",
            inv_sudo.id,
            _("Invoice signed by %s") % (name,),
            attachments=[("%s.pdf" % inv_sudo.name, pdf)],
            **({"token": access_token} if access_token else {})
        )

        query_string = "&message=sign_ok"
        if inv_sudo.has_to_be_paid(True):
            query_string += "#allow_payment=yes&#portal_pay=yes"
        return {
            "force_refresh": True,
            "redirect_url": inv_sudo.get_portal_url(query_string=query_string),
        }
