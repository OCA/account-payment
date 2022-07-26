# Copyright (C) 2022, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI


class PaymentTransaction(models.Model):
    _inherit = ["mail.thread", "payment.transaction"]
    _name = "payment.transaction"

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        return super().message_post(**kwargs)

    def _set_txn_log_notes(self, response):
        message = _("""A transaction %s response: %s.""")
        message_vals = (self.reference, str(response))
        post_message = message % message_vals
        self.message_post(body=post_message)

    # Overwrite the odoo addons -> payment_authorize module method
    def authorize_s2s_do_transaction(self, **data):
        self.ensure_one()
        if not self.acquirer_id.debug:
            return super(PaymentTransaction, self).authorize_s2s_do_transaction(**data)
        transaction = AuthorizeAPI(self.acquirer_id)

        if not self.payment_token_id.authorize_profile:
            raise UserError(
                _(
                    "Invalid token found: the Authorize profile is missing."
                    "Please make sure the token has a valid acquirer reference."
                )
            )

        if not self.acquirer_id.capture_manually:
            res = transaction.auth_and_capture(
                self.payment_token_id,
                round(self.amount, self.currency_id.decimal_places),
                self.reference,
            )
        else:
            res = transaction.authorize(
                self.payment_token_id,
                round(self.amount, self.currency_id.decimal_places),
                self.reference,
            )
        self._set_txn_log_notes(res)
        return self._authorize_s2s_validate_tree(res)

    # Overwrite the odoo addons -> payment_authorize module method
    def authorize_s2s_capture_transaction(self):
        self.ensure_one()
        if not self.acquirer_id.debug:
            return super(PaymentTransaction, self).authorize_s2s_capture_transaction()
        transaction = AuthorizeAPI(self.acquirer_id)
        tree = transaction.capture(
            self.acquirer_reference or "",
            round(self.amount, self.currency_id.decimal_places),
        )
        self._set_txn_log_notes(tree)
        return self._authorize_s2s_validate_tree(tree)

    # Overwrite the odoo addons -> payment_authorize module method
    def authorize_s2s_void_transaction(self):
        self.ensure_one()
        if not self.acquirer_id.debug:
            return super(PaymentTransaction, self).authorize_s2s_void_transaction()
        transaction = AuthorizeAPI(self.acquirer_id)
        tree = transaction.void(self.acquirer_reference or "")
        self._set_txn_log_notes(tree)
        return self._authorize_s2s_validate_tree(tree)
