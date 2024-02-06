# Copyright 2022 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ["account.payment","mail.thread"]

    def mark_as_sent(self):
        """Auto-notify when marking as sent."""
        result = super().mark_as_sent()
        if self.company_id.account_payment_notification_automatic != "manual":
            self._notify_sent_payments_auto()
        return result

    @api.multi
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
            ):
                to_sms |= payment
            if method == "email_or_sms" and payment.partner_id.email:
                to_sms -= payment
            elif method == "sms_or_email":
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

    @api.multi
    def _notify_sent_payments_email(self):
        """Notify sent payments by email."""
        mt_comment = self.env.ref("mail.mt_comment")
        tpl = self.env.ref("account_payment_notification.mail_template_notification")
        assert tpl.model == self._name, "Template has wrong model!?"
        for payment in self:
            # TODO Batch per lang if possible
            payment.message_post_with_template(
                tpl.id,
                composition_mode="mass_post",
                subtype_id=mt_comment.id,
                notify=True,
            )

    @api.model
    def get_email_to(self):
        """ Return a valid email for customer """
        contact = self.partner_id
        email = contact.email
        if not email and contact.commercial_partner_id.email:
            email = contact.commercial_partner_id.email
        return email

    @api.model
    def get_contact_address(self):
        partner_obj = self.env['res.partner']
        partner = self.partner_id
        add_ids = partner.address_get(adr_pref=['invoice']) or {}
        add_id = add_ids['invoice']
        if add_id:
            return partner_obj.browse(add_id)       
        else:
            return partner

    @api.model
    def get_invoice_names(self):
        res = ""
        for inv in self.mapped("invoice_ids"):
            res += inv.number
            res += "\n"
        return res
