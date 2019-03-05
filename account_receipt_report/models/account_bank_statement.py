# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def action_print_invoice_payment(self):
        # Print the report based in account.move.lines
        receipt_report = self.env.ref(
            'account_receipt_report.action_account_report_payment_receipt')
        account_move_lines = self.journal_entry_ids.filtered(
            lambda x: x.account_id.internal_type in ['receivable', 'payable']
        )
        if account_move_lines:
            return receipt_report.report_action(account_move_lines.ids)
