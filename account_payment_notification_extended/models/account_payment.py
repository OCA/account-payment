from odoo import api, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model
    def _cron_notify_payments(self):
        """Notify payments matching the configured company domain."""
        companies = (
            self.env["res.company"]
            .sudo()
            .search([("account_payment_notification_automatic", "=", "auto")])
        )
        for company in companies:
            domain = company._get_account_payment_notification_domain()
            payments = (
                self.env["account.payment"].sudo().with_company(company).search(domain)
            )
            payments.mark_as_sent()
