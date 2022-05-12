# Copyright 2023 ForgeFlow S.L. (http://www.forgeflow.com)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_check_printing_layout = fields.Selection(
        selection_add=[
            (
                "account_check_printing_report_sslm102.action_report_check_sslm102",
                "sslm102",
            )
        ],
        ondelete={
            "account_check_printing_report_sslm102.action_report_check_sslm102": "cascade"
        },
    )
