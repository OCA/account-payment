# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pending_due_date = fields.Date(
        string="Remaining due days",
        compute="_compute_pending_due_date",
        help="The date when the payment is due, or empty if it's done.",
    )

    @api.depends("date_maturity", "matching_number")
    def _compute_pending_due_date(self):
        """Establish due date for pending payments.

        If a payment is matched, it means it's paid. We empty the field if the
        payment is done, so the `remaining_days` widget is nicer for the user.
        """
        matched = self.filtered("matching_number")
        matched.pending_due_date = False
        for move in self - matched:
            move.pending_due_date = move.date_maturity
