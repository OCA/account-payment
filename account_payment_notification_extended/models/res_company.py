from ast import literal_eval

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_payment_notification_domain = fields.Char(
        string="Payment notification domain",
        default="[]",
        help="Domain used to select payments for automatic notification.",
    )
    account_payment_notification_start_date = fields.Date(
        string="Payment notification start date",
        help="Only payments from this date onwards will be notified.",
    )

    def _get_account_payment_notification_static_domain(self):
        """Return the static domain for payment notifications."""
        self.ensure_one()

        domain = [
            ("state", "not in", ["draft", "cancel"]),
            ("is_sent", "=", False),
            ("company_id", "=", self.id),
        ]

        if self.account_payment_notification_start_date:
            domain.append(("date", ">=", self.account_payment_notification_start_date))

        return domain

    def _get_account_payment_notification_domain(self):
        """Return the configured domain for payment notification."""
        self.ensure_one()

        return self._get_account_payment_notification_static_domain() + literal_eval(
            self.account_payment_notification_domain or "[]"
        )
