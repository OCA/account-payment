# © 2016 Eficent Business and IT Consulting Services S.L.
# Copyright 2018 iterativo.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountCheckPrintingReportBase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.account_invoice_model = self.env["account.move"]
        self.journal_model = self.env["account.journal"]
        self.payment_method_model = self.env["account.payment.method"]
        self.account_account_model = self.env["account.account"]
        self.payment_model = self.env["account.payment"]
        self.report = self.env[
            "report.account_check_printing_report_base.report_check_base"
        ]

        self.partner1 = self.env.ref("base.res_partner_1")
        self.company = self.env.ref("base.main_company")
        self.currency_usd_id = self.env.ref("base.USD").id
        self.currency_euro_id = self.env.ref("base.EUR").id
        self.acc_payable = self.env.ref("account.data_account_type_payable")
        self.acc_expense = self.env.ref("account.data_account_type_expenses")
        self.product = self.env.ref("product.product_product_4")
        self.check_report = self.env.ref(
            "account_check_printing_report_base.account_payment_check_report_base"
        )
        self.action_check_report = self.env.ref(
            "account_check_printing_report_base.action_report_check_base"
        )

        self.check_report_by_journal = self.check_report.copy(
            {"name": "Test Check Layout By Journal"}
        )
        self.payment_method_check = self.payment_method_model.search(
            [("code", "=", "check_printing")],
            limit=1,
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
            {"name": "Purchase Journal - Test", "type": "purchase", "code": "Test"}
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
                "move_type": "in_invoice",
                "partner_id": self.partner1.id,
                "currency_id": self.company.currency_id.id,
                "journal_id": self.purchase_journal.id,
                "company_id": self.company.id,
                "invoice_date": fields.Date.today(),
            }
        )
        return vendor_bill

    def _create_invoice_line(self, account, invoice):
        invoice = invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test invoice line",
                            "account_id": account.id,
                            "quantity": 1.000,
                            "price_unit": 2.99,
                            "product_id": self.product.id,
                        },
                    )
                ]
            }
        )

        return invoice

    def test_02_check_printing_with_layout(self):
        """Test if the check is printed when the layout is specified for a
        company and journal."""

        self.company.check_layout_id = self.check_report
        acc_payable = self._create_account(
            "account payable test", "ACPRB1", self.acc_payable, True
        )
        vendor_bill = self._create_vendor_bill(acc_payable)
        acc_expense = self._create_account(
            "account expense test", "ACPRB2", self.acc_expense, False
        )
        self._create_invoice_line(acc_expense, vendor_bill)
        vendor_bill.action_post()
        ctx = {"active_model": "account.move", "active_ids": [vendor_bill.id]}
        register_payments = self.payment_model.with_context(ctx).create(
            {
                "date": time.strftime("%Y") + "-07-15",
                "journal_id": self.bank_journal.id,
                "payment_method_id": self.payment_method_check.id,
            }
        )
        register_payments.action_post()
        payment = self.payment_model.search([], order="id desc", limit=1)
        payment.journal_id.check_layout_id = self.check_report_by_journal

        e = False
        try:
            payment.print_checks()
        except UserError as e:
            e = e.name
        self.assertEqual(e, False)

        content = self.action_check_report._render_qweb_pdf(payment.id)
        self.assertEqual(content[1], "html")

    def test_03_fotmat_form(self):
        """Test formatting on check form"""
        # Convert date to formatting from partner : 2020-01-20 > 01/20/2020
        today = fields.Date.today()
        date = self.report._format_date_to_partner_lang(today, self.partner1.id)
        self.assertEqual(date, today.strftime("%m/%d/%Y"))
        # Fill starts in amount
        amount = 100.0
        amount_in_word = "One Hundred Euro"
        stars = 100 - len(amount_in_word)
        amount_in_word = "One Hundred Euro"
        large_amount_in_word = "ten hundred billion  ten hundred million  \
            fifty thousand eleven hundred  eleven ruppes eleven cent euro"
        amount1 = self.report.fill_stars_number(str(amount))
        amount2 = self.report.fill_stars(amount_in_word)
        amount3 = self.report.fill_stars(large_amount_in_word)
        self.assertEqual(amount1, "***** %s *" % amount)
        self.assertEqual(amount2, "{} {}".format(amount_in_word, ("*" * stars)))
        self.assertEqual(amount3, large_amount_in_word)

    def test_03_res_amount(self):
        register_payments = self.payment_model.create(
            {
                "date": time.strftime("%Y") + "-07-15",
                "journal_id": self.bank_journal.id,
                "payment_method_id": self.payment_method_check.id,
                "amount": 1000,
            }
        )
        register_payments.action_post()
        payment = self.payment_model.search([], order="id desc", limit=1)
        for aml in payment.line_ids:
            total_amt = self.report._get_total_amount(payment, aml)
            residual_amt = self.report._get_residual_amount(payment, aml)
            paid_amt = self.report._get_paid_amount(payment, aml)
            self.assertEqual(paid_amt, 0)
            self.assertEqual(residual_amt, 1000)
            self.assertEqual(total_amt, 1000)
