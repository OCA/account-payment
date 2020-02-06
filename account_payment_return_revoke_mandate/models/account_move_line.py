# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    @api.multi
    def _payment_returned(self, return_line):
        super()._payment_returned(return_line)
        if return_line.reason_id.revoke_mandates:
            for rec in self:
                if rec.mandate_id:
                    try:
                        rec.mandate_id.cancel()
                        msg = (
                            "Mandate revoked in payment return %s"
                            % return_line.return_id.name
                        )
                        rec.mandate_id.message_post(body=msg)
                    except UserError:
                        # May happen if the mandate is not draft or valid
                        pass
