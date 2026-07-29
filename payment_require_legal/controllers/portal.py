# Copyright 2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentPortal


class PaymentPortalLegal(PaymentPortal):
    @staticmethod
    def _validate_transaction_kwargs(kwargs, additional_allowed_keys=()):
        return super(
            PaymentPortalLegal, PaymentPortalLegal
        )._validate_transaction_kwargs(
            kwargs,
            additional_allowed_keys=(
                *additional_allowed_keys,
                "legal_terms_accepted",
            ),
        )

    def _create_transaction(self, *args, **kwargs):
        legal_terms_accepted = kwargs.pop("legal_terms_accepted", False)
        if legal_terms_accepted:
            environ = request.httprequest.environ
            custom_create_values = kwargs.setdefault("custom_create_values", {})
            custom_create_values["legal_terms_acceptance_metadata"] = "\n".join(
                f"{key}: {environ.get(key)}"
                for key in (
                    "REMOTE_ADDR",
                    "HTTP_USER_AGENT",
                    "HTTP_ACCEPT_LANGUAGE",
                )
            )
        return super()._create_transaction(*args, **kwargs)
