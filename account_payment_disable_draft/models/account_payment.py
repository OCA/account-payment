# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _get_disable_reset_to_draft(self):
        ICP = self.env["ir.config_parameter"]
        disable_reset = ICP.sudo().get_param("account_payment.disable_reset_to_draft")
        return disable_reset

    def action_draft(self):
        """Check state payment 'cancel' not allow reset to draft"""
        for rec in self:
            if self._get_disable_reset_to_draft() and rec.state == "cancel":
                raise UserError(_("Not allowed to reset draft on payment."))
        return super().action_draft()
