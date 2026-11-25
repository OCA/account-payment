from datetime import timedelta

from odoo import fields
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountPaymentNotificationExtended(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                allowed_company_ids=cls.company.ids,
            )
        )
        cls.partner = cls.partner_a
        cls.partner.write({"email": "test@example.com"})
        cls.company.account_payment_notification_automatic = "auto"
        invoice = cls.init_invoice(
            "out_invoice",
            partner=cls.partner,
            post=True,
            amounts=[100],
        )
        action = invoice.action_register_payment()
        form = Form(
            cls.env[action["res_model"]].with_context(
                mail_create_nolog=True,
                **action["context"],
            )
        )
        cls.payments = form.save()._create_payments()

    def test_static_domain(self):
        domain = self.company._get_account_payment_notification_static_domain()
        self.assertIn(
            ("state", "not in", ["draft", "cancel"]),
            domain,
        )
        self.assertIn(
            ("is_sent", "=", False),
            domain,
        )
        self.assertIn(
            ("company_id", "=", self.company.id),
            domain,
        )

    def test_configured_domain(self):
        self.company.account_payment_notification_domain = (
            "[('partner_id', '=', %d)]" % self.partner.id
        )
        domain = self.company._get_account_payment_notification_domain()
        self.assertIn(
            ("partner_id", "=", self.partner.id),
            domain,
        )

    def test_cron_notifies_matching_payments(self):
        self.assertFalse(self.payments.filtered("is_sent"))
        self.env["account.payment"]._cron_notify_payments()
        self.assertTrue(all(self.payments.mapped("is_sent")))

    def test_cron_does_not_notify_sent_payments(self):
        self.company.account_payment_notification_automatic = "manual"
        self.payments.mark_as_sent()
        self.company.account_payment_notification_automatic = "auto"
        self.assertTrue(all(self.payments.mapped("is_sent")))
        self.env["account.payment"]._cron_notify_payments()
        self.assertTrue(all(self.payments.mapped("is_sent")))

    def test_cron_respects_start_date(self):
        self.company.account_payment_notification_start_date = (
            fields.Date.today() + timedelta(days=1)
        )
        self.env["account.payment"]._cron_notify_payments()
        self.assertFalse(self.payments.filtered("is_sent"))
        self.company.account_payment_notification_start_date = (
            fields.Date.today() - timedelta(days=1)
        )
        self.env["account.payment"]._cron_notify_payments()
        self.assertTrue(all(self.payments.mapped("is_sent")))

    def test_cron_only_processes_automatic_companies(self):
        self.company.account_payment_notification_automatic = "manual"
        self.env["account.payment"]._cron_notify_payments()
        self.assertFalse(self.payments.filtered("is_sent"))
