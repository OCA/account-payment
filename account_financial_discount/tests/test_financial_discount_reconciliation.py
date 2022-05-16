# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from freezegun import freeze_time

from odoo.tests.common import Form

from .common import TestAccountFinancialDiscountCommon


@freeze_time("2019-05-01")
class TestAccountFinancialDiscountReconciliation(TestAccountFinancialDiscountCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client_invoice1 = cls.init_invoice(
            cls.customer,
            "out_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-05-01",
            invoice_date_due="2019-06-01",
        )
        cls.init_invoice_line(cls.client_invoice1, 1.0, 1000.0)

        cls.reconciliation_model = cls.env["account.reconcile.model"].search(
            [("rule_type", "=", "invoice_matching")], limit=1
        )
        cls.reconciliation_model.write(
            {
                "match_partner": False,
                # "strict_match_total_amount": True,
                "apply_financial_discounts": True,
                "financial_discount_tolerance": 0.05,
            }
        )

        cls.amount_taxed_without_discount = 1150.0
        cls.amount_taxed_discount = 23.0
        cls.amount_taxed_with_discount = 1127.0
        cls.amount_discount_tax = 3.0

        cls.amount_untaxed_without_discount = 1000.0
        cls.amount_untaxed_discount = 20.0
        cls.amount_untaxed_with_discount = 980.0

    def _create_bank_statement(self, journal=None):
        if journal is None:
            journal = self.bank_journal
        bank_statement_form = Form(self.env["account.bank.statement"])
        bank_statement_form.name = "Test Reconcile Financial Discount"
        bank_statement_form.journal_id = journal
        return bank_statement_form.save()

    def _create_bank_statement_line(self, bank_statement, label, amount):
        with Form(bank_statement) as statement_form:
            with statement_form.line_ids.new() as statement_line_form:
                statement_line_form.payment_ref = label
                statement_line_form.amount = amount

    def test_client_invoice_with_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            invoice_date_due="2019-06-01",
        )
        self.init_invoice_line(invoice, 1.0, self.amount_untaxed_without_discount)
        invoice.action_post()
        invoice_receivable_line = invoice._get_first_payment_term_line()
        invoice_tax_line = invoice.line_ids.filtered(lambda l: l.tax_line_id)
        bank_statement = self._create_bank_statement()
        self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_taxed_with_discount
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [invoice_receivable_line.id]
        )
        self.assertEqual(matching_amls.get(st_line.id).get("status"), "write_off")
        write_off_vals = matching_amls.get(st_line.id).get("write_off_vals")
        self.assertEqual(
            write_off_vals[0].get("name"),
            self.reconciliation_model.financial_discount_label,
        )
        self.assertEqual(
            write_off_vals[0].get("account_id"),
            self.reconciliation_model.financial_discount_expense_account_id.id,
        )
        self.assertEqual(write_off_vals[0].get("debit"), self.amount_untaxed_discount)
        self.assertEqual(
            write_off_vals[1].get("name"),
            self.reconciliation_model.financial_discount_label
            + " "
            + invoice_tax_line.name,
        )
        self.assertEqual(
            write_off_vals[1].get("account_id"), invoice_tax_line.account_id.id
        )
        self.assertEqual(write_off_vals[1].get("debit"), self.amount_discount_tax)

    def test_client_invoice_without_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            invoice_date_due="2019-06-01",
        )
        self.init_invoice_line(
            invoice, 1.0, self.amount_untaxed_without_discount, with_tax=False
        )
        invoice.action_post()
        invoice_receivable_line = invoice._get_first_payment_term_line()
        bank_statement = self._create_bank_statement()
        self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_untaxed_with_discount
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [invoice_receivable_line.id]
        )
        self.assertEqual(matching_amls.get(st_line.id).get("status"), "write_off")
        write_off_vals = matching_amls.get(st_line.id).get("write_off_vals")
        self.assertEqual(
            write_off_vals[0].get("name"),
            self.reconciliation_model.financial_discount_label,
        )
        self.assertEqual(
            write_off_vals[0].get("account_id"),
            self.reconciliation_model.financial_discount_expense_account_id.id,
        )
        self.assertEqual(write_off_vals[0].get("debit"), self.amount_untaxed_discount)

    def test_vendor_bill_with_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            invoice_date_due="2019-06-01",
            payment_reference="VENDOR-BILL-REF-0001",
        )
        self.init_invoice_line(vendor_bill, 1.0, self.amount_untaxed_without_discount)
        vendor_bill.action_post()
        vendor_bill_payable_line = vendor_bill._get_first_payment_term_line()
        vendor_bill_tax_line = vendor_bill.line_ids.filtered(lambda l: l.tax_line_id)
        bank_statement = self._create_bank_statement()
        self._create_bank_statement_line(
            bank_statement,
            vendor_bill.payment_reference,
            -self.amount_taxed_with_discount,
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [vendor_bill_payable_line.id]
        )
        self.assertEqual(matching_amls.get(st_line.id).get("status"), "write_off")
        write_off_vals = matching_amls.get(st_line.id).get("write_off_vals")
        self.assertEqual(
            write_off_vals[0].get("name"),
            self.reconciliation_model.financial_discount_label,
        )
        self.assertEqual(
            write_off_vals[0].get("account_id"),
            self.reconciliation_model.financial_discount_revenue_account_id.id,
        )
        self.assertEqual(write_off_vals[0].get("credit"), self.amount_untaxed_discount)
        self.assertEqual(
            write_off_vals[1].get("name"),
            self.reconciliation_model.financial_discount_label
            + " "
            + vendor_bill_tax_line.name,
        )
        self.assertEqual(
            write_off_vals[1].get("account_id"), vendor_bill_tax_line.account_id.id
        )
        self.assertEqual(write_off_vals[1].get("credit"), self.amount_discount_tax)

    def test_vendor_bill_without_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            invoice_date_due="2019-06-01",
            payment_reference="VENDOR-BILL-REF-0001",
        )
        self.init_invoice_line(
            vendor_bill,
            1.0,
            self.amount_untaxed_without_discount,
            with_tax=False,
        )
        vendor_bill.action_post()
        vendor_bill_payable_line = vendor_bill._get_first_payment_term_line()
        bank_statement = self._create_bank_statement()
        self._create_bank_statement_line(
            bank_statement,
            vendor_bill.payment_reference,
            -self.amount_untaxed_with_discount,
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [vendor_bill_payable_line.id]
        )
        self.assertEqual(matching_amls.get(st_line.id).get("status"), "write_off")
        write_off_vals = matching_amls.get(st_line.id).get("write_off_vals")
        self.assertEqual(
            write_off_vals[0].get("name"),
            self.reconciliation_model.financial_discount_label,
        )
        self.assertEqual(
            write_off_vals[0].get("account_id"),
            self.reconciliation_model.financial_discount_revenue_account_id.id,
        )
        self.assertEqual(write_off_vals[0].get("credit"), self.amount_untaxed_discount)

    def test_client_invoice_with_tax_late_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-03-01",
            invoice_date_due="2019-04-01",
        )
        self.init_invoice_line(invoice, 1.0, self.amount_untaxed_without_discount)
        invoice.action_post()
        invoice_receivable_line = invoice._get_first_payment_term_line()
        bank_statement = self._create_bank_statement()
        self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_taxed_with_discount
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [invoice_receivable_line.id]
        )
        self.assertFalse(matching_amls.get(st_line.id).get("status"))

    def test_vendor_bill_with_tax_late_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-03-01",
            invoice_date_due="2019-04-01",
            payment_reference="VENDOR-BILL-REF-0001",
        )
        self.init_invoice_line(vendor_bill, 1.0, self.amount_untaxed_without_discount)
        vendor_bill.action_post()
        vendor_bill_payable_line = vendor_bill._get_first_payment_term_line()
        bank_statement = self._create_bank_statement()
        self._create_bank_statement_line(
            bank_statement,
            vendor_bill.payment_reference,
            -self.amount_taxed_with_discount,
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [vendor_bill_payable_line.id]
        )
        self.assertFalse(matching_amls.get(st_line.id).get("status"))

    def test_client_invoice_with_tax_late_forced_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-03-01",
            invoice_date_due="2019-04-01",
        )
        self.init_invoice_line(invoice, 1.0, self.amount_untaxed_without_discount)
        invoice.action_post()
        invoice_receivable_line = invoice._get_first_payment_term_line()
        invoice_tax_line = invoice.line_ids.filtered(lambda l: l.tax_line_id)
        invoice.force_financial_discount = True
        bank_statement = self._create_bank_statement()
        self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_taxed_with_discount
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [invoice_receivable_line.id]
        )
        self.assertEqual(matching_amls.get(st_line.id).get("status"), "write_off")
        write_off_vals = matching_amls.get(st_line.id).get("write_off_vals")
        self.assertEqual(
            write_off_vals[0].get("name"),
            self.reconciliation_model.financial_discount_label,
        )
        self.assertEqual(
            write_off_vals[0].get("account_id"),
            self.reconciliation_model.financial_discount_expense_account_id.id,
        )
        self.assertEqual(write_off_vals[0].get("debit"), self.amount_untaxed_discount)
        self.assertEqual(
            write_off_vals[1].get("name"),
            self.reconciliation_model.financial_discount_label
            + " "
            + invoice_tax_line.name,
        )
        self.assertEqual(
            write_off_vals[1].get("account_id"), invoice_tax_line.account_id.id
        )
        self.assertEqual(write_off_vals[1].get("debit"), self.amount_discount_tax)

    def test_vendor_bill_with_tax_late_forced_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-03-01",
            invoice_date_due="2019-04-01",
            payment_reference="VENDOR-BILL-REF-0001",
        )
        self.init_invoice_line(vendor_bill, 1.0, self.amount_untaxed_without_discount)
        vendor_bill.action_post()
        vendor_bill_payable_line = vendor_bill._get_first_payment_term_line()
        vendor_bill_tax_line = vendor_bill.line_ids.filtered(lambda l: l.tax_line_id)
        vendor_bill.force_financial_discount = True
        bank_statement = self._create_bank_statement()
        self._create_bank_statement_line(
            bank_statement,
            vendor_bill.payment_reference,
            -self.amount_taxed_with_discount,
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [vendor_bill_payable_line.id]
        )
        self.assertEqual(matching_amls.get(st_line.id).get("status"), "write_off")
        write_off_vals = matching_amls.get(st_line.id).get("write_off_vals")
        self.assertEqual(
            write_off_vals[0].get("name"),
            self.reconciliation_model.financial_discount_label,
        )
        self.assertEqual(
            write_off_vals[0].get("account_id"),
            self.reconciliation_model.financial_discount_revenue_account_id.id,
        )
        self.assertEqual(write_off_vals[0].get("credit"), self.amount_untaxed_discount)
        self.assertEqual(
            write_off_vals[1].get("name"),
            self.reconciliation_model.financial_discount_label
            + " "
            + vendor_bill_tax_line.name,
        )
        self.assertEqual(
            write_off_vals[1].get("account_id"), vendor_bill_tax_line.account_id.id
        )
        self.assertEqual(write_off_vals[1].get("credit"), self.amount_discount_tax)

    def test_client_invoice_eur_with_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            invoice_date_due="2019-06-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice, 1.0, self.amount_untaxed_without_discount)
        invoice.action_post()
        invoice_receivable_line = invoice._get_first_payment_term_line()
        invoice_tax_line = invoice.line_ids.filtered(lambda l: l.tax_line_id)
        bank_statement = self._create_bank_statement(journal=self.eur_bank_journal)
        self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_taxed_with_discount
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [invoice_receivable_line.id]
        )
        write_off_vals = matching_amls.get(st_line.id).get("write_off_vals")
        self.assertEqual(
            write_off_vals[0].get("name"),
            self.reconciliation_model.financial_discount_label,
        )
        self.assertEqual(
            write_off_vals[0].get("account_id"),
            self.reconciliation_model.financial_discount_expense_account_id.id,
        )
        self.assertEqual(
            write_off_vals[0].get("debit"),
            self.eur_currency._convert(
                self.amount_untaxed_discount,
                self.usd_currency,
                invoice.company_id,
                invoice.invoice_date,
            ),
        )
        self.assertEqual(
            write_off_vals[1].get("name"),
            self.reconciliation_model.financial_discount_label
            + " "
            + invoice_tax_line.name,
        )
        self.assertEqual(
            write_off_vals[1].get("account_id"), invoice_tax_line.account_id.id
        )
        self.assertEqual(
            write_off_vals[1].get("debit"),
            self.eur_currency._convert(
                self.amount_discount_tax,
                self.usd_currency,
                invoice.company_id,
                invoice.invoice_date,
            ),
        )

    def test_vendor_bill_eur_with_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-05-01",
            invoice_date_due="2019-06-01",
            currency=self.eur_currency,
            payment_reference="VENDOR-BILL-REF-0001",
        )
        self.init_invoice_line(vendor_bill, 1.0, self.amount_untaxed_without_discount)
        vendor_bill.action_post()
        vendor_bill_payable_line = vendor_bill._get_first_payment_term_line()
        vendor_bill_tax_line = vendor_bill.line_ids.filtered(lambda l: l.tax_line_id)
        bank_statement = self._create_bank_statement(journal=self.eur_bank_journal)
        self._create_bank_statement_line(
            bank_statement,
            vendor_bill.payment_reference,
            -self.amount_taxed_with_discount,
        )
        st_line = bank_statement.line_ids
        matching_amls = self.reconciliation_model._apply_rules(st_line)
        self.assertEqual(
            matching_amls.get(st_line.id).get("aml_ids"), [vendor_bill_payable_line.id]
        )
        write_off_vals = matching_amls.get(st_line.id).get("write_off_vals")
        self.assertEqual(
            write_off_vals[0].get("name"),
            self.reconciliation_model.financial_discount_label,
        )
        self.assertEqual(
            write_off_vals[0].get("account_id"),
            self.reconciliation_model.financial_discount_revenue_account_id.id,
        )
        self.assertEqual(
            write_off_vals[0].get("credit"),
            self.eur_currency._convert(
                self.amount_untaxed_discount,
                self.usd_currency,
                vendor_bill.company_id,
                vendor_bill.invoice_date,
            ),
        )
        self.assertEqual(
            write_off_vals[1].get("name"),
            self.reconciliation_model.financial_discount_label
            + " "
            + vendor_bill_tax_line.name,
        )
        self.assertEqual(
            write_off_vals[1].get("account_id"), vendor_bill_tax_line.account_id.id
        )
        self.assertEqual(
            write_off_vals[1].get("credit"),
            self.eur_currency._convert(
                self.amount_discount_tax,
                self.usd_currency,
                vendor_bill.company_id,
                vendor_bill.invoice_date,
            ),
        )

    # TODO add more tests with banking reconciliation:
    #  - Auto-reconcile on the model
