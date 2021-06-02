# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class AccountJournal(models.Model):

    _inherit = "account.journal"

    use_payment_terminal = fields.Selection(
        selection=lambda self: self._get_payment_terminal_selection(),
        string="Use a Payment Terminal",
        help="Record payments with a terminal on this journal.",
    )

    def _get_payment_terminal_selection(self):
        return [("oca_payment_terminal", _("OCA Payment Terminal"))]
