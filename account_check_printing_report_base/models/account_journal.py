# Copyright 2017 Tecnativa.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from .res_company import REPORTS_DEFINED


class AccountJournal(models.Model):
    _inherit = "account.journal"

    check_print_auto = fields.Boolean(
        string="Automatic check printing",
        help="Default check for the company is printed automatically when "
        "invoice payment is validated",
    )
    account_check_printing_layout = fields.Selection(
        string="Check Layout",
        selection=REPORTS_DEFINED,
        # Set default False to allow using same ondelete as res.company when inheriting
        # this module.
        default=False,
        help="Select the format corresponding to the check paper you will be printing "
        "your checks on.\n"
        "In order to disable the printing feature, select 'None'.",
    )
