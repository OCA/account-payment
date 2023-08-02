# Copyright 2022 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import TestAccountReconciliationCommon


@tagged("post_install", "-at_install")
class NotificationCase(TestAccountReconciliationCommon):
    def setUp(self):
        super().setUp()
        self.company = self.company_data["company"]
        # Partners with different communication methods
        self.partner_a.write({"email": "a@example.com", "mobile": "+1 111 111 111"})
        self.partner_b.write({"email": "b@example.com", "mobile": False})
        self.partner_c = self.partner_a.copy(
            {"email": False, "mobile": "+3 333 333 333", "name": "partner_c"}
        )
        # Restricted accountant should be able to do the rest of stuff

        self.env.user.groups_id = self.env.ref(
            "account.group_account_manager"
        ) + self.env.ref("base.group_partner_manager")
        # Create invoices
        self.invoices = (
            self.create_invoice_partner(partner_id=self.partner_a.id)
            + self.create_invoice_partner(partner_id=self.partner_a.id)
            + self.create_invoice_partner(partner_id=self.partner_b.id)
            + self.create_invoice_partner(partner_id=self.partner_c.id)
        )
        # Create 3 payments
        action = self.invoices.action_register_payment()
        form = Form(
            self.env[action["res_model"]].with_context(
                mail_create_nolog=True, **action["context"]
            )
        )
        form.group_payment = True
        self.payments = form.save()._create_payments()

    def set_mode(self, mode):
        """Set automated notifications mode for company."""
        form = Form(self.env["res.config.settings"].sudo())
        form.account_payment_notification_method = mode
        form.save()

    def assert_notifications(self, partners, email=False, sms=False):
        """Assert the notifications are sent as expected."""
        mt_comment = self.env.ref("mail.mt_comment")
        for payment in self.payments.filtered(lambda rec: rec.partner_id in partners):
            expected_values = []
            expected_message_notifications = []
            if sms:
                expected_values.append(
                    {
                        "message_type": "sms",
                        "description": "Dear {}, the [...]".format(
                            payment.partner_id.name
                        ),
                    }
                )
                expected_message_notifications.append(
                    {
                        "res_partner_id": payment.partner_id.id,
                        "notification_type": "sms",
                        "notification_status": "ready",
                    }
                )
            if email:
                expected_values.append(
                    {
                        "message_type": "notification",
                        "description": "{} Payment Notification (Ref {})".format(
                            payment.company_id.name, payment.name
                        ),
                        "subtype_id": mt_comment.id,
                    }
                )
                expected_message_notifications.append(
                    {
                        "res_partner_id": payment.partner_id.id,
                        "notification_type": "email",
                        "notification_status": "ready",
                    }
                )
            if expected_values:
                self.assertRecordValues(payment.message_ids, expected_values)
            else:
                self.assertFalse(payment.message_ids)
            # Assert notifications, so UI displays the envelope icon and send status
            if expected_message_notifications:
                self.assertRecordValues(
                    payment.message_ids.notification_ids, expected_message_notifications
                )
            else:
                self.assertFalse(payment.message_ids.notification_ids)

    @mute_logger("odoo.tests.common.onchange")
    def test_auto_all(self):
        """Emails and SMS are sent to customers."""
        self.set_mode("all")
        self.assertFalse(self.payments.message_ids)
        self.payments.mark_as_sent()
        self.assert_notifications(self.partner_a, email=True, sms=True)
        self.assert_notifications(self.partner_b, email=True)
        self.assert_notifications(self.partner_c, sms=True)

    def test_auto_disabled(self):
        """Nothing is automatically sent to customers."""
        self.company.sudo().account_payment_notification_automatic = "manual"
        self.assertFalse(self.payments.message_ids)
        self.payments.mark_as_sent()
        self.assert_notifications(self.partner_a)
        self.assert_notifications(self.partner_b)
        self.assert_notifications(self.partner_c)

    def test_auto_email_only(self):
        """Only emails are sent to customers."""
        # This is the default mode
        self.assertEqual(
            self.env.company.account_payment_notification_method, "email_only"
        )
        self.payments.mark_as_sent()
        self.assert_notifications(self.partner_a, email=True)
        self.assert_notifications(self.partner_b, email=True)
        self.assert_notifications(self.partner_c)

    @mute_logger("odoo.tests.common.onchange")
    def test_auto_email_or_sms(self):
        """Emails are preferably sent to customers."""
        self.set_mode("email_or_sms")
        self.payments.mark_as_sent()
        self.assert_notifications(self.partner_a, email=True)
        self.assert_notifications(self.partner_b, email=True)
        self.assert_notifications(self.partner_c, sms=True)

    @mute_logger("odoo.tests.common.onchange")
    def test_auto_sms_only(self):
        """Only SMS are sent to customers."""
        self.set_mode("sms_only")
        self.payments.mark_as_sent()
        self.assert_notifications(self.partner_a, sms=True)
        self.assert_notifications(self.partner_b)
        self.assert_notifications(self.partner_c, sms=True)

    @mute_logger("odoo.tests.common.onchange")
    def test_auto_sms_or_email(self):
        """SMS are preferably sent to customers."""
        self.set_mode("sms_or_email")
        self.payments.mark_as_sent()
        self.assert_notifications(self.partner_a, sms=True)
        self.assert_notifications(self.partner_b, email=True)
        self.assert_notifications(self.partner_c, sms=True)

    @mute_logger("odoo.tests.common.onchange")
    def test_no_contact(self):
        """Partners without contact means make it fail."""
        self.partner_b.email = False
        self.partner_c.mobile = False
        self.company.sudo().account_payment_notification_required = True
        self.set_mode("all")
        with self.assertRaises(
            ValidationError,
            msg="Cannot notify partners of these payments: {}, {}".format(
                self.payments[0].display_name, self.payments[1].display_name
            ),
        ):
            self.payments.mark_as_sent()

    @mute_logger("odoo.tests.common.onchange")
    def test_multilang(self):
        """Multiple notifications sent in each partner email."""
        self.env["res.lang"].sudo()._activate_lang("es_ES")
        mail_tpl = self.env.ref(
            "account_payment_notification.mail_template_notification"
        )
        sms_tpl = self.env.ref("account_payment_notification.sms_template_notification")
        mail_tpl.subject = "English mail"
        sms_tpl.sudo().body = "English SMS"
        mail_tpl.with_context(lang="es_ES").subject = "Spanish mail"
        sms_tpl.with_context(lang="es_ES").sudo().body = "Spanish SMS"
        self.partner_a.lang = "es_ES"
        self.set_mode("all")
        self.payments.mark_as_sent()
        self.assertRecordValues(
            self.payments.message_ids,
            [
                {"message_type": "sms", "description": "English SMS"},
                {"message_type": "notification", "description": "English mail"},
                {"message_type": "sms", "description": "Spanish SMS"},
                {"message_type": "notification", "description": "Spanish mail"},
            ],
        )
