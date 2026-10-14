# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move"

    def _payment_returned(self, return_line):
        res = super()._payment_returned(return_line)
        if return_line.reason_id.revoke_mandates:
            self._revoke_mandate(return_line)
        return res

    def _revoke_mandate(self, return_line):
        for rec in self:
            if rec.mandate_id:
                try:
                    rec.mandate_id.cancel()
                    msg = _(
                        "Mandate revoked in payment return %s",
                        return_line.return_id.name,
                    )
                    rec.mandate_id.message_post(body=msg)
                except UserError:
                    # May happen if the mandate is not draft or valid
                    _logger.error(
                        "Trying to revoke mandate %s from payment return %s but it"
                        " has the state %s.",
                        rec.mandate_id.unique_mandate_reference,
                        return_line.return_id.name,
                        rec.mandate_id.state,
                    )
