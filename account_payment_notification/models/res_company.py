# Copyright 2022 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from ast import literal_eval

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_payment_notification_automatic = fields.Selection(
        string="Payment notifications automatism",
        required=True,
        default="auto",
        selection=[
            ("manual", "Notify manually"),
            ("auto", "Notify automatically"),
        ],
        help="Choose the automatism level when notifying sent payments.",
    )
    account_payment_notification_method = fields.Selection(
        string="Payment notification method",
        required=True,
        default="email_only",
        selection=[
            ("email_only", "By email"),
            ("email_or_sms", "By email if possible, by SMS otherwise"),
            ("sms_only", "By SMS"),
            ("sms_or_email", "By SMS if possible, by email otherwise"),
            ("all", "By all possible notification means"),
        ],
        help="Choose the method to notify payments automatically when marked as sent.",
    )
    account_payment_notification_required = fields.Boolean(
        string="Require payment notifications",
        help=(
            "Enable to forbid marking payments as sent if they cannot be "
            "notified using the chosen method(s)."
        ),
    )
    account_payment_notification_domain = fields.Char(
        string="Payment notification domain",
        default="[]",
        help="Domain used to select payments for automatic notification.",
    )

    def _get_account_payment_notification_static_domain(self):
        """Return the static domain for payment notifications."""
        self.ensure_one()
        return [
            ("state", "not in", ["draft", "cancel"]),
            ("is_sent", "=", False),
            ("company_id", "=", self.id),
        ]

    def _get_account_payment_notification_domain(self):
        """Return the configured domain for payment notification."""
        self.ensure_one()
        return self._get_account_payment_notification_static_domain() + literal_eval(
            self.account_payment_notification_domain or "[]"
        )
