# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_print_invoice_payment(self):
        # Print the report
        receipt_report = self.env.ref(
            'account_receipt_report.action_account_report_payment_receipt')
        account_move_lines = self.move_line_ids.filtered(
            lambda x: x.account_id.internal_type in ['receivable', 'payable']
        )
        return receipt_report.report_action(account_move_lines.ids)

    def action_validate_print_invoice_payment(self):
        self.action_validate_invoice_payment()
        return self.action_print_invoice_payment()
