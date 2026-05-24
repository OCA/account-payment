# 2016-2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from functools import reduce

from odoo import fields
from odoo.tests.common import TransactionCase


class TestAccountCheckReport(TransactionCase):
    def setUp(self):
        super(TestAccountCheckReport, self).setUp()
        self.journal_model = self.env["account.journal"]
        self.account_move_model = self.env["account.move"]
        self.account_move_line_model = self.env["account.move.line"]
        self.register_payments_model = self.env["account.payment.register"]
        self.payment_method_model = self.env["account.payment.method"]
        self.account_account_model = self.env["account.account"]
        self.payment_model = self.env["account.payment"]
        self.payment_method_line_model = self.env["account.payment.method.line"]

        self.partner1 = self.env.ref("base.res_partner_1")
        self.company = self.env.ref("base.main_company")
        self.currency_usd_id = self.env.ref("base.USD").id
        self.currency_euro_id = self.env.ref("base.EUR").id
        self.acc_payable_type = self.env.ref("account.data_account_type_payable")
        self.acc_expense_type = self.env.ref("account.data_account_type_expenses")
        self.product = self.env.ref("product.product_product_4")
        self.payment_method_check = self.payment_method_model.search(
            [("code", "=", "check_printing")],
            limit=1,
        )
        self.action_check_report = self.env.ref(
            "account_check_report.action_report_check_report"
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
        self.bank_journal = self.journal_model.create(
            {
                "name": "Cash Journal - Test",
                "type": "bank",
                "code": "bank",
                "check_manual_sequencing": True,
                "outbound_payment_method_line_ids": [
                    (4, self.payment_method_check.id, None)
                ],
            }
        )
        self.payment_method_line_check = self.payment_method_line_model.create(
            {
                "name": "Check",
                "payment_method_id": self.payment_method_check.id,
                "journal_id": self.bank_journal.id,
            }
        )
        self.purchase_journal = self.journal_model.create(
            {
                "name": "Purchase Journal - Test",
                "type": "purchase",
                "code": "Test",
            }
        )
        self.acc_payable = self._create_account(
            "account payable test", "ACPRB1", self.acc_payable_type, True
        )
        self.acc_expense = self._create_account(
            "account expense test", "ACPRB2", self.acc_expense_type, False
        )
        self.partner1.property_account_payable_id = self.acc_payable

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
        partner_id = self.partner1.id
        invoice_vals = {
            "move_type": "in_invoice",
            "partner_id": partner_id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Test product",
                        "quantity": 1,
                        "account_id": account.id,
                        "price_unit": 2.99,
                        "tax_ids": [(6, 0, [])],
                    },
                )
            ],
        }
        invoice = (
            self.env["account.move"]
            .with_context(default_move_type="out_invoice")
            .create(invoice_vals)
        )
        return invoice

    def _create_payment(self, amount=1.0):
        payment = self.payment_model.create(
            {
                "payment_type": "outbound",
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "partner_type": "supplier",
                "partner_id": self.partner1.id,
                "amount": amount,
                "currency_id": self.company.currency_id.id,
                "date": time.strftime("%Y-%m-%d"),
                "journal_id": self.bank_journal.id,
                "company_id": self.company.id,
            }
        )
        payment.action_post()
        return payment

    def test_01_check_printing(self):
        """Test if the report is printed succesfully"""
        vendor_bill = self._create_vendor_bill(self.acc_expense)
        vendor_bill.action_post()
        wiz = self.register_payments_model.with_context(
            active_ids=[vendor_bill.id], active_model="account.move"
        ).create(
            {
                "journal_id": self.bank_journal.id,
                "payment_date": fields.Date.from_string("2077-10-23"),
                "group_payment": True,
                "payment_method_line_id": self.payment_method_line_check.id,
            }
        )
        payment = wiz._create_payments()
        content = self.action_check_report._render_qweb_pdf(payment.id)
        self.assertEqual(content[1], "html")

    def test_02_get_invoices(self):
        """Test if the lines shown are good (simple case)"""
        vendor_bill = self._create_vendor_bill(self.acc_expense)
        vendor_bill2 = self._create_vendor_bill(self.acc_expense)
        vendor_bill.action_post()
        vendor_bill2.action_post()
        wiz = self.register_payments_model.with_context(
            active_ids=[vendor_bill.id, vendor_bill2.id], active_model="account.move"
        ).create(
            {
                "journal_id": self.bank_journal.id,
                "payment_date": fields.Date.from_string("2077-10-23"),
                "group_payment": True,
                "payment_method_line_id": self.payment_method_line_check.id,
            }
        )
        payment = wiz._create_payments()
        amls = self.env["report.account_check_report.check_report"]._get_paid_lines(
            payment
        )
        amml_list = [item[0] for item in amls]
        self.assertIn(
            vendor_bill.line_ids.filtered(lambda l: l.account_id == self.acc_payable),
            amml_list,
        )
        self.assertTrue(
            len(
                vendor_bill.line_ids.filtered(
                    lambda l: l.account_id == self.acc_payable
                )
            )
            > 0
        )
        #  Test button invoices
        res = payment.button_open_bills()
        self.assertTrue(vendor_bill.id in res["domain"][1][2])

    def test_03_several_payments(self):
        """check the amount is correct on partial payments
        and the line is not repeated if several payments involved"""
        vendor_bill = self._create_vendor_bill(self.acc_expense)
        vendor_bill.action_post()
        vendor_bill2 = self._create_vendor_bill(self.acc_expense)
        vendor_bill2.action_post()
        payment = self._create_payment(amount=1)
        payment2 = self._create_payment(amount=4)
        payment_ml = payment.line_ids.filtered(
            lambda l: l.account_id == self.acc_payable
        )
        payment2_ml = payment2.line_ids.filtered(
            lambda l: l.account_id == self.acc_payable
        )
        vendor_bill_ml = vendor_bill.line_ids.filtered(
            lambda l: l.account_id == self.acc_payable
        )
        vendor_bill2_ml = vendor_bill2.line_ids.filtered(
            lambda l: l.account_id == self.acc_payable
        )
        # reconcile fully the first bill with 1st payment
        # the rest with the 2nd payment 1 + 1.99
        (payment_ml + payment2_ml + vendor_bill_ml).reconcile()
        # reconcile partially the 2nd payments with the second invoice ($ 2.01 from payment)
        (payment2_ml + vendor_bill2_ml).reconcile()
        # PAYMENT CHECK REPORT PAYMENT 1
        report_lines = self.env[
            "report.account_check_report.check_report"
        ]._get_paid_lines(payment)
        amls_in_report = reduce(lambda x, y: x + y, report_lines)
        aml_list = [item[0] for item in amls_in_report]
        # check only the first bill appears
        self.assertIn(
            vendor_bill.line_ids.filtered(lambda l: l.account_id == self.acc_payable),
            aml_list,
        )
        self.assertNotIn(
            vendor_bill2.line_ids.filtered(lambda l: l.account_id == self.acc_payable),
            aml_list,
        )
        # check the values of the line in the report
        paid_amount = self.env[
            "report.account_check_report.check_report"
        ]._get_paid_amount_this_payment(payment, amls_in_report)
        self.assertEqual(paid_amount, 1.0)
        residual = self.env[
            "report.account_check_report.check_report"
        ]._get_residual_amount(payment, amls_in_report)
        self.assertEqual(residual, 0.0)
        total_amount = self.env[
            "report.account_check_report.check_report"
        ]._get_total_amount(payment, amls_in_report)
        self.assertEqual(total_amount, 2.99)
        # PAYMENT CHECK REPORT PAYMENT 2
        report_lines = self.env[
            "report.account_check_report.check_report"
        ]._get_paid_lines(payment2)
        amls_in_report = reduce(lambda x, y: x + y, report_lines)
        aml_list = [item[0] for item in amls_in_report]
        # check both bill appears
        self.assertIn(
            vendor_bill.line_ids.filtered(lambda l: l.account_id == self.acc_payable),
            aml_list,
        )
        self.assertIn(
            vendor_bill2.line_ids.filtered(lambda l: l.account_id == self.acc_payable),
            aml_list,
        )
        # check the values of the line in the report
        for aml in amls_in_report:
            paid_amount = self.env[
                "report.account_check_report.check_report"
            ]._get_paid_amount_this_payment(payment2, aml)
            if aml == vendor_bill_ml:
                self.assertAlmostEqual(paid_amount, 1.99, places=2)
            else:
                self.assertAlmostEqual(paid_amount, 2.01, places=2)
            residual = self.env[
                "report.account_check_report.check_report"
            ]._get_residual_amount(payment2, aml)
            if aml == vendor_bill_ml:
                self.assertEqual(residual, 0.0)
            else:
                self.assertAlmostEqual(residual, 0.98, places=2)
            total_amount = self.env[
                "report.account_check_report.check_report"
            ]._get_total_amount(payment2, aml)
            self.assertAlmostEqual(total_amount, 2.99, places=2)
