# Copyright 2022 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class NotificationCase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.accountman = cls.env["res.users"].search([("login", "=", "accountman")])
        cls.env = cls.env(
            user=cls.accountman,
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids),
        )
        # Partners with different communication methods
        cls.partner_a.write({"email": "a@example.com", "mobile": "+1 111 111 111"})
        cls.partner_b.write({"email": "b@example.com", "mobile": False})
        cls.partner_c = cls.partner_a.copy(
            {"email": False, "mobile": "+3 333 333 333", "name": "partner_c"}
        )
        # Restricted accountant should be able to do the rest of stuff

        cls.env.user.groups_id = cls.env.ref(
            "account.group_account_manager"
        ) + cls.env.ref("base.group_partner_manager")
        # Create invoices
        cls.invoices = (
            cls.init_invoice(
                "out_invoice", partner=cls.partner_a, post=True, amounts=[50]
            )
            + cls.init_invoice(
                "out_invoice", partner=cls.partner_a, post=True, amounts=[50]
            )
            + cls.init_invoice(
                "out_invoice", partner=cls.partner_b, post=True, amounts=[50]
            )
            + cls.init_invoice(
                "out_invoice", partner=cls.partner_c, post=True, amounts=[50]
            )
        )
        # Create 3 payments
        action = cls.invoices.action_register_payment()
        form = Form(
            cls.env[action["res_model"]].with_context(
                mail_create_nolog=True, **action["context"]
            )
        )
        form.group_payment = True
        cls.payments = form.save()._create_payments()

    def set_mode(self, mode):
        """Set automated notifications mode for company."""
        self.company.sudo().account_payment_notification_method = mode

    def assert_email_notifications(self, partners):
        """Assert the email notifications are sent as expected."""
        mt_comment = self.env.ref("mail.mt_comment")
        payments = self.payments.filtered(lambda rec: rec.partner_id in partners)
        expected_values = []
        expected_message_notifications = []
        for payment in payments:
            expected_values = [
                {
                    "subject": (
                        f"{payment.company_id.name} Payment Notification "
                        f"(Ref {payment.name})"
                    ),
                    "subtype_id": mt_comment.id,
                }
            ]
            expected_message_notifications = [
                {
                    "res_partner_id": payment.partner_id.id,
                    "notification_type": "email",
                    "notification_status": ("ready" if len(partners) > 1 else "sent"),
                }
            ]
        msgs = payments.message_ids.filtered(
            lambda msg: msg.message_type == "notification"
        )
        self.assertRecordValues(msgs, expected_values)
        self.assertRecordValues(msgs.notification_ids, expected_message_notifications)

    def assert_sms_notifications(self, partners):
        """Assert the SMS notifications are sent as expected."""
        sms_tpl = self.env.ref("account_payment_notification.sms_template_notification")
        payments = self.payments.filtered(lambda rec: rec.partner_id in partners)
        expected_sms_bodies = []
        expected_message_notifications = []
        for payment in payments:
            expected_sms_bodies.append(
                sms_tpl._render_field("body", payment.ids, compute_lang=True)[
                    payment.id
                ]
            )
            expected_message_notifications.append(
                {
                    "res_partner_id": payment.partner_id.id,
                    "notification_type": "sms",
                    "notification_status": "ready",
                }
            )
        msgs = payments.message_ids.filtered(lambda msg: msg.message_type == "sms")
        self.assertRecordValues(msgs.notification_ids, expected_message_notifications)
        # Assert SMS bodies, handled as a special case because the message body is
        # stored as HTML but the SMS template is rendered as plain text
        for sms_notification, expected_body in zip(
            msgs, expected_sms_bodies, strict=True
        ):
            self.assertHTMLEqual(sms_notification.body, expected_body)

    def assert_notifications(self, partners, email=False, sms=False):
        """Assert the notifications are sent as expected."""
        if email:
            self.assert_email_notifications(partners)
            if not sms:
                with self.assertRaises(
                    AssertionError,
                    msg="SMS notifications should not be sent",
                ):
                    self.assert_sms_notifications(partners)
        if sms:
            self.assert_sms_notifications(partners)
            if not email:
                with self.assertRaises(
                    AssertionError,
                    msg="Email notifications should not be sent",
                ):
                    self.assert_email_notifications(partners)

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
            self.env.company.account_payment_notification_automatic, "auto"
        )
        self.set_mode("email_only")
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
            msg=(
                "Cannot notify partners of these payments: "
                f"{self.payments[0].display_name}, {self.payments[1].display_name}"
            ),
        ):
            self.payments.mark_as_sent()

    @mute_logger("odoo.tests.common.onchange")
    def test_multilang(self):
        """Multiple notifications sent in each partner email."""
        self.env["res.lang"].sudo()._activate_lang("es_ES")
        mail_tpl = self.env.ref(
            "account_payment_notification.mail_template_notification"
        ).sudo()
        sms_tpl = self.env.ref(
            "account_payment_notification.sms_template_notification"
        ).sudo()
        mail_tpl.subject = "English mail"
        sms_tpl.body = "English SMS"
        mail_tpl.with_context(lang="es_ES").subject = "Spanish mail"
        sms_tpl.with_context(lang="es_ES").body = "Spanish SMS"
        self.partner_a.lang = "es_ES"
        self.set_mode("all")
        self.payments.mark_as_sent()
        sms_msgs = self.payments.message_ids.filtered(
            lambda msg: msg.message_type == "sms"
        )
        email_msgs = self.payments.message_ids - sms_msgs
        self.assertRecordValues(
            email_msgs,
            [
                {"message_type": "notification", "subject": "English mail"},
                {"message_type": "notification", "subject": "Spanish mail"},
            ],
        )
        self.assertRecordValues(sms_msgs, [{"message_type": "sms"}] * 2)
        self.assertHTMLEqual(sms_msgs[0].body, "English SMS")
        self.assertHTMLEqual(sms_msgs[1].body, "Spanish SMS")
