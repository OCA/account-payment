# Copyright 2023 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    account_check_printing_layout = fields.Selection(
        selection_add=[
            (
                "account_check_printing_report_dlt103.action_report_check_dlt103",
                "dlt103",
            )
        ],
        ondelete={
            "account_check_printing_report_dlt103.action_report_check_dlt103": "cascade"
        },
    )
