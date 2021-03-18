# Copyright 2017 Tecnativa - luis M. Ontalba
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    default_expense_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Default Charges Account",
        help="Default account for bank charges",
    )
    default_expense_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Default Charges Partner",
        help="Default partner for charge expenses",
    )
    return_auto_reconcile = fields.Boolean(
        string="Reconcile payment returns",
        help="Enable automatic payment return reconciliation. This option "
        "is meant to be used only when working with transfer accounts, "
        "not if working directly with bank accounts.",
        default=False,
    )
