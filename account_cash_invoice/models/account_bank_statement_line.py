# Copyright (C) 2017-2021 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    invoice_id = fields.Many2one(
        comodel_name="account.move", string="Invoice", readonly=True,
    )

    def fast_counterpart_creation(self):
        for st_line in self:
            if not st_line.invoice_id:
                super(AccountBankStatementLine, st_line).fast_counterpart_creation()
            else:
                invoice = st_line.invoice_id
                move_line = invoice.line_ids.filtered(
                    lambda r: r.exclude_from_invoice_tab
                    and r.account_id.user_type_id.type in ("receivable", "payable")
                )
                vals = {
                    "name": st_line.name,
                    "debit": st_line.amount < 0 and -st_line.amount or 0.0,
                    "credit": st_line.amount > 0 and st_line.amount or 0.0,
                    "move_line": move_line,
                }
                st_line.process_reconciliation(counterpart_aml_dicts=[vals])
