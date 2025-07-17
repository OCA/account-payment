# Copyright 2022 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # Used by sms.composer to get default phone
    mobile = fields.Char(related="partner_id.mobile")

    def mark_as_sent(self):
        """Auto-notify when marking as sent."""
        result = super().mark_as_sent()
        if self.company_id.account_payment_notification_automatic != "manual":
            self._notify_sent_payments_auto()
        return result

    def _notify_sent_payments_auto(self):
        """Notify sent payments choosing method automatically."""
        to_email = to_sms = self.browse()
        method = self.company_id.account_payment_notification_method
        # Select automated notification modes
        for payment in self:
            if (
                method in {"all", "email_only", "email_or_sms", "sms_or_email"}
                and payment.partner_id.email
            ):
                to_email |= payment
            if (
                method in {"all", "email_or_sms", "sms_only", "sms_or_email"}
                and payment.mobile
            ):
                to_sms |= payment
            if method == "email_or_sms" and payment.partner_id.email:
                to_sms -= payment
            elif method == "sms_or_email" and payment.mobile:
                to_email -= payment
        # Fail if auto-notifying is required
        not_notified = self - to_email - to_sms
        if not_notified and self.company_id.account_payment_notification_required:
            raise ValidationError(
                _(
                    "Cannot notify partners of these payments: %s",
                    ", ".join(not_notified.mapped("display_name")),
                )
            )
        # Send notifications
        to_email._notify_sent_payments_email()
        to_sms._notify_sent_payments_sms()

    def _notify_sent_payments_email(self):
        """Notify sent payments by email."""
        mt_comment = self.env.ref("mail.mt_comment")
        tpl = self.env.ref("account_payment_notification.mail_template_notification")
        assert tpl.model == self._name, "Template has wrong model!?"
        self.message_post_with_source(tpl, subtype_id=mt_comment.id)

    def _notify_sent_payments_sms(self):
        """Notify sent payments by sms."""
        tpl = self.env.ref("account_payment_notification.sms_template_notification")
        assert tpl.model == self._name, "Template has wrong model!?"
        for payment in self:
            # TODO Batch per lang if possible
            payment._message_sms_with_template(
                tpl, partner_ids=payment.partner_id.ids, put_in_queue=True
            )
