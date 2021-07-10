# Copyright 2021 Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    destination_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Destination Journal",
        domain="[('type', 'in', ['bank', 'cash']), "
        "('company_id', '=', company_id), ('id', '!=', journal_id)]",
    )
    paired_internal_transfer_payment_id = fields.Many2one(
        comodel_name="account.payment",
        help="When an internal transfer is posted, a paired payment is created. "
        "They cross referenced trough this field",
    )

    def action_post(self):
        res = super().action_post()
        self.filtered(
            lambda pay: pay.is_internal_transfer
            and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()
        return res

    def _create_paired_internal_transfer_payment(self):
        """When an internal transfer is posted, a paired payment is created
        with opposite payment_type and swapped journal_id & destination_journal_id.
        Both payments liquidity transfer lines are then reconciled.
        """
        for payment in self:

            paired_payment = payment.copy(
                {
                    "journal_id": payment.destination_journal_id.id,
                    "destination_journal_id": payment.journal_id.id,
                    "payment_type": payment.payment_type == "outbound"
                    and "inbound"
                    or "outbound",
                    "move_id": None,
                    "ref": payment.ref,
                    "paired_internal_transfer_payment_id": payment.id,
                }
            )
            paired_payment.move_id._post(soft=False)
            payment.paired_internal_transfer_payment_id = paired_payment

            body = _(
                "This payment has been created from "
                "<a href=# data-oe-model=account.payment data-oe-id=%(id)s>%(name)s</a>"
            ) % {"id": payment.id, "name": payment.name}
            paired_payment.message_post(body=body)
            body = _(
                "A second payment has been created: <a href=# data-oe-model=account.payment "
                "data-oe-id=%(id)s>%(name)s</a>"
            ) % {"id": paired_payment.id, "name": paired_payment.name}
            payment.message_post(body=body)

            lines = (
                payment.move_id.line_ids + paired_payment.move_id.line_ids
            ).filtered(
                lambda l: l.account_id == payment.destination_account_id
                and not l.reconciled
            )
            lines.reconcile()
