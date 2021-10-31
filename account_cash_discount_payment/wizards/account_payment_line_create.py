# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountPaymentLineCreate(models.TransientModel):

    _inherit = "account.payment.line.create"

    date_type = fields.Selection(
        selection_add=[("discount_due_date", _("Discount Due Date"))],
        ondelete={"discount_due_date": "cascade"},
    )
    cash_discount_date = fields.Date(
        default=lambda self: fields.Date.today(),
        help="Search lines with a discount due date which is posterior to "
        "the selected date.",
    )

    @api.onchange(
        "date_type",
        "move_date",
        "due_date",
        "journal_ids",
        "invoice",
        "target_move",
        "allow_blocked",
        "payment_mode",
        "cash_discount_date",
    )
    def move_line_filters_change(self):
        return super(AccountPaymentLineCreate, self).move_line_filters_change()

    def _prepare_move_line_domain(self):
        self.ensure_one()
        domain = super(AccountPaymentLineCreate, self)._prepare_move_line_domain()

        if self.date_type == "discount_due_date":
            due_date = self.cash_discount_date
            domain += [
                ("move_id.discount_due_date", ">=", due_date),
            ]
        return domain
