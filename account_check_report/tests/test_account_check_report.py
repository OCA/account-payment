# -*- coding: utf-8 -*-
# 2016-2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
import time


class TestAccountCheckReport(TransactionCase):
    def setUp(self):
        super(TestAccountCheckReport, self).setUp()
        self.account_invoice_model = self.env["account.invoice"]
        self.journal_model = self.env["account.journal"]
        self.register_payments_model = self.env["account.register.payments"]
        self.payment_method_model = self.env["account.payment.method"]
        self.account_invoice_line_model = self.env["account.invoice.line"]
        self.account_account_model = self.env["account.account"]
        self.payment_model = self.env["account.payment"]

        self.partner1 = self.env.ref("base.res_partner_1")
        self.company = self.env.ref("base.main_company")
        self.currency_usd_id = self.env.ref("base.USD").id
        self.currency_euro_id = self.env.ref("base.EUR").id
        self.acc_payable = self.env.ref("account.data_account_type_payable")
        self.acc_expense = self.env.ref("account.data_account_type_expenses")
        self.product = self.env.ref("product.product_product_4")
        self.payment_method_check = self.payment_method_model.search(
            [("code", "=", "check_printing")], limit=1,
        )
        if not self.payment_method_check:
            self.payment_method_check = self.payment_method_model.create(
                {
                    "name": "Check",
                    "code": "check_printing",
                    "payment_type": "outbound",
                    "check": True,
                }
            )
        self.purchase_journal = self.journal_model.create(
            {
                "name": "Purchase Journal - Test",
                "type": "purchase",
                "code": "Test",
            }
        )
        self.bank_journal = self.journal_model.create(
            {
                "name": "Cash Journal - Test",
                "type": "bank",
                "code": "bank",
                "check_manual_sequencing": True,
                "outbound_payment_method_ids": [
                    (4, self.payment_method_check.id, None)
                ],
            }
        )

    def _create_account(self, name, code, user_type, reconcile):
        account = self.account_account_model.create(
            {
                "name": name,
                "code": code,
                "user_type_id": user_type.id,
                "company_id": self.company.id,
                "reconcile": reconcile,
            }
        )
        return account

    def _create_vendor_bill(self, account):
        vendor_bill = self.account_invoice_model.create(
            {
                "type": "in_invoice",
                "partner_id": self.partner1.id,
                "account_id": account.id,
                "currency_id": self.company.currency_id.id,
                "journal_id": self.purchase_journal.id,
                "company_id": self.company.id,
            }
        )
        return vendor_bill

    def _create_invoice_line(self, account, invoice):
        invoice_line = self.account_invoice_line_model.create(
            {
                "name": "Test invoice line",
                "account_id": account.id,
                "quantity": 1.000,
                "price_unit": 2.99,
                "invoice_id": invoice.id,
                "product_id": self.product.id,
            }
        )
        return invoice_line

    def test_01_check_printing(self):
        """ Test if the report is printed succesfully"""
        acc_payable = self._create_account(
            "account payable test", "ACPRB1", self.acc_payable, True
        )
        vendor_bill = self._create_vendor_bill(acc_payable)
        acc_expense = self._create_account(
            "account expense test", "ACPRB2", self.acc_expense, False
        )
        self._create_invoice_line(acc_expense, vendor_bill)
        vendor_bill.action_invoice_open()
        ctx = {
            "active_model": "account.invoice",
            "active_ids": [vendor_bill.id],
        }
        register_payments = self.register_payments_model.with_context(
            ctx
        ).create(
            {
                "payment_date": time.strftime("%Y") + "-07-15",
                "journal_id": self.bank_journal.id,
                "payment_method_id": self.payment_method_check.id,
            }
        )
        register_payments.create_payment()
        payment = self.payment_model.search([], order="id desc", limit=1)
        e = False
        try:
            self.env[
                "report.account_check_report.check_report"
            ].render_html(payment.id,)
        except UserError as e:
            pass
        self.assertEquals(e, False)

    def test_02_get_invoices(self):
        """ Test if the lines shown are good"""
        acc_payable = self._create_account(
            "account payable test", "ACPRB1", self.acc_payable, True
        )
        vendor_bill = self._create_vendor_bill(acc_payable)
        acc_expense = self._create_account(
            "account expense test", "ACPRB2", self.acc_expense, False
        )
        self._create_invoice_line(acc_expense, vendor_bill)
        vendor_bill.action_invoice_open()
        ctx = {
            "active_model": "account.invoice",
            "active_ids": [vendor_bill.id],
        }
        register_payments = self.register_payments_model.with_context(
            ctx
        ).create(
            {
                "payment_date": time.strftime("%Y") + "-07-15",
                "journal_id": self.bank_journal.id,
                "payment_method_id": self.payment_method_check.id,
            }
        )
        register_payments.create_payment()
        payment = self.payment_model.search([], order="id desc", limit=1)
        amls = self.env[
            "report.account_check_report.check_report"
        ]._get_paid_lines(payment)
        self.assertTrue(
            vendor_bill.move_id.line_ids.filtered(
                lambda l: l.account_id == acc_payable
            )
            in amls[0]
        )
        #  Test button invoices
        domain_inv = payment.button_invoices()
        self.assertTrue(vendor_bill.id in domain_inv['domain'][1][2])
