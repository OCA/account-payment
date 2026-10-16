# Copyright 2026 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    installment_count = fields.Integer(
        string="Number of Installments",
        default=1,
        help="When set greater than 1, the payment term lines are regenerated"
        " automatically as equal installments separated by the configured"
        " interval in days. The last line is always the balance.",
    )
    installment_interval_days = fields.Integer(
        string="Days Between Installments",
        default=30,
        help="Number of days added between each installment. The first"
        " installment is due after this many days.",
    )

    @api.constrains("installment_count", "installment_interval_days")
    def _check_installment_values(self):
        for term in self:
            if term.installment_count < 1:
                raise ValidationError(_("Number of installments must be at least 1."))
            if term.installment_interval_days < 0:
                raise ValidationError(
                    _("Days between installments must be zero or positive.")
                )

    @api.onchange("installment_count", "installment_interval_days")
    def _onchange_installment_count(self):
        if self.installment_count and self.installment_count > 1:
            self._generate_installment_lines()

    def _generate_installment_lines(self):
        self.ensure_one()
        count = self.installment_count or 1
        interval = self.installment_interval_days or 0
        commands = [Command.clear()]
        if count > 1:
            percent = 100.0 / count
            for i in range(1, count):
                commands.append(
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": percent,
                            "days": interval * i,
                        }
                    )
                )
        commands.append(
            Command.create(
                {
                    "value": "balance",
                    "days": interval * count if count > 1 else 0,
                }
            )
        )
        self.line_ids = commands
