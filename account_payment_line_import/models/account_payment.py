# Copyright 2023 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from contextlib import suppress

from odoo import api, models


class AccountPayment(models.Model):

    _inherit = "account.payment"

    @api.model
    def load(self, fields, data):
        account_move = self.env["account.move"]
        if "template_context" in self.env.context and self.env.context.get(
            "active_id", False
        ):
            fields.append("line_payment_counterpart_ids/partner_id")
            current_payment = self.browse(self.env.context.get("active_id"))
            current_payment.action_delete_counterpart_lines()
            current_partner = current_payment.partner_id
            new_data = []
            for line in data:
                # Description
                if len(line[1]) == 0:
                    line[1] = "/"
                # Invoice / Refund
                if len(line[2]) != 0:
                    # Can be ID
                    with suppress(ValueError):
                        invoice_id = int(line[2])
                        invoice = account_move.browse(invoice_id)
                        line[2] = invoice.name
                        line.append(invoice.partner_id.display_name)
                # Account
                if len(line[4]) == 0:
                    if current_payment.destination_account_id:
                        line[4] = current_payment.destination_account_id.code
                # If partner not on invoice search by ID
                if len(line) != len(fields):
                    line.append(current_partner.display_name)
                new_data.append(line)
            data = new_data
        return super().load(fields, data)

    def post_import_process_lines(self):
        for line in self.line_payment_counterpart_ids.filtered(lambda x: x.move_id):
            current_amount = line.amount
            current_description = line.name
            line._onchange_move_id()
            line.name = current_description
            line.amount = current_amount
        return True
