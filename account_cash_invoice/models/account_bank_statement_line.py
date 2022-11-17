# Copyright (C) 2017-2021 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        readonly=True,
        index=True,
    )
