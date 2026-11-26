# Copyright 2016 ForgeFlow, S.L.
# (http://www.forgeflow.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

REPORTS_DEFINED = [
    ("account_check_printing_report_base.action_report_check_base", "Print Check Base"),
    (
        "account_check_printing_report_base.action_report_check_base_a4",
        "Print Check Base A4",
    ),
]
REPORTS_DEFINED_ONDELETE = {r[0]: "set default" for r in REPORTS_DEFINED}


class ResCompany(models.Model):
    _inherit = "res.company"

    account_check_printing_layout = fields.Selection(
        selection_add=REPORTS_DEFINED, ondelete=REPORTS_DEFINED_ONDELETE
    )
