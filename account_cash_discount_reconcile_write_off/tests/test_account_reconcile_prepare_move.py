from odoo.fields import Date
from odoo.tools.misc import format_date

from odoo.addons.account_cash_discount_payment.tests.common import (
    TestAccountCashDiscountPaymentCommon,
)


class TestAccountReconcilePrepareMove(TestAccountCashDiscountPaymentCommon):
    def test_prepare_move(self):
        self.Reconcile = self.env["account.reconciliation.widget"]
        invoice_date = Date.today()
        invoice = self.create_supplier_invoice(
            invoice_date, self.payment_mode_out, 1000, 25, []
        )
        invoice.action_post()
        move_line_list = self.Reconcile._prepare_move_lines(
            invoice.line_ids, self.company.currency_id
        )
        self.assertEquals("$\xa0250.00", move_line_list[0]["discount_amount"])
        self.assertEquals(
            format_date(self.env, invoice_date), move_line_list[0]["discount_due_date"]
        )

    def test_prepare_move_bad_company_currency(self):
        self.Reconcile = self.env["account.reconciliation.widget"]
        invoice_date = Date.today()
        invoice = self.create_supplier_invoice(
            invoice_date, self.payment_mode_out, 1000, 25, []
        )
        invoice.action_post()
        move_line_list = self.Reconcile._prepare_move_lines(invoice.line_ids)
        self.assertEquals("250.00", move_line_list[0]["discount_amount"])
        self.assertEquals(
            format_date(self.env, invoice_date), move_line_list[0]["discount_due_date"]
        )
