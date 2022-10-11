# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import Form

from .common import TestAccountFinancialDiscountCommon


@freeze_time("2019-04-01")
class TestAccountFinancialDiscountManualPayment(TestAccountFinancialDiscountCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice1 = cls.init_invoice(
            cls.partner,
            "in_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.invoice1, 1.0, 1000.0)

        cls.invoice2 = cls.init_invoice(
            cls.partner,
            "in_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
        )
        cls.init_invoice_line(cls.invoice2, 1.0, 1000.0)

        cls.invoice3 = cls.init_invoice(
            cls.partner,
            "in_invoice",
            payment_term=cls.payment_thirty_net,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.invoice3, 1.0, 1000.0)

        cls.client_invoice1 = cls.init_invoice(
            cls.customer,
            "out_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.client_invoice1, 1.0, 1000.0)

        cls.client_invoice2 = cls.init_invoice(
            cls.customer,
            "out_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
        )
        cls.init_invoice_line(cls.client_invoice2, 1.0, 1000.0)

        cls.client_invoice3 = cls.init_invoice(
            cls.customer,
            "out_invoice",
            payment_term=cls.payment_thirty_net,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.client_invoice3, 1.0, 1000.0)

        cls.amount_without_discount = 1150.0
        cls.amount_discount = 23.0
        cls.amount_with_discount = 1127.0

    def _assert_payment_line_with_discount_from_invoice(self, invoice):
        invoice_payment_line = self._get_payment_lines(invoice)
        # The payment move line must have full amount to set invoice as paid
        self.assertEqual(
            invoice_payment_line.amount_currency, self.amount_without_discount
        )
        invoice_payment = invoice_payment_line.mapped("payment_id")
        # The payment must have the amount with discount
        self.assertEqual(invoice_payment.amount, self.amount_with_discount)
        for payment_line in invoice_payment_line.move_id.line_ids:
            if payment_line == invoice_payment_line:
                continue
            elif payment_line.account_id in (self.write_off_rev, self.write_off_exp):
                # Write off line must have the discount amount and label
                self.assertEqual(payment_line.amount_currency, -self.amount_discount)
                self.assertEqual(payment_line.name, "Financial Discount")
            else:
                # Oustanding payment line must have the amount with discount
                self.assertEqual(
                    payment_line.amount_currency, -self.amount_with_discount
                )

    def test_invoice_discount_term_line(self):
        """Test saving of discount on payment term line for vendor bills"""
        invoice = self.init_invoice(
            self.partner,
            "in_invoice",
            self.payment_term,
            invoice_date="2019-04-15",
            invoice_date_due="2019-05-15",
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        # self.assertEqual(invoice.date, fields.Date.to_date("2019-04-01"))
        # self.assertFalse(invoice.invoice_date)
        with freeze_time("2019-04-15"):
            invoice.action_post()
            self.assertEqual(invoice.date, fields.Date.to_date("2019-04-15"))
            self.assertEqual(invoice.invoice_date, fields.Date.to_date("2019-04-15"))
            self.assertTrue(invoice.has_discount_available)
            term_line = invoice.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type == "payable"
            )
            self.assertEqual(term_line.date_discount, fields.Date.to_date("2019-04-25"))
            self.assertEqual(term_line.amount_discount, -self.amount_discount)

    def test_customer_invoice_discount_term_line(self):
        """Test saving of discount on payment term line for customer invoice"""
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            self.payment_term,
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        self.assertEqual(invoice.date, fields.Date.to_date("2019-04-01"))
        self.assertFalse(invoice.invoice_date)
        with freeze_time("2019-04-15"):
            invoice.action_post()
            self.assertEqual(invoice.date, fields.Date.to_date("2019-04-15"))
            self.assertEqual(invoice.invoice_date, fields.Date.to_date("2019-04-15"))
            self.assertTrue(invoice.has_discount_available)
            term_line = invoice.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type == "receivable"
            )
            self.assertEqual(term_line.date_discount, fields.Date.to_date("2019-04-25"))
            self.assertEqual(term_line.amount_discount, self.amount_discount)

    def test_invoice_discount_term_line_multicurrency(self):
        """
        Test saving of discount on payment term line for multi currency vendor bills
        """
        invoice = self.init_invoice(
            self.partner,
            "in_invoice",
            self.payment_term,
            currency=self.eur_currency,
            invoice_date="2019-04-15",
            invoice_date_due="2019-05-15",
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        # self.assertEqual(invoice.date, fields.Date.to_date("2019-04-01"))
        # self.assertFalse(invoice.invoice_date)
        with freeze_time("2019-04-15"):
            invoice.action_post()
            self.assertEqual(invoice.date, fields.Date.to_date("2019-04-15"))
            self.assertEqual(invoice.invoice_date, fields.Date.to_date("2019-04-15"))
            self.assertTrue(invoice.has_discount_available)
            term_line = invoice.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type == "payable"
            )
            self.assertEqual(term_line.date_discount, fields.Date.to_date("2019-04-25"))
            self.assertEqual(
                term_line.amount_discount,
                -self.eur_currency._convert(
                    self.amount_discount,
                    self.usd_currency,
                    invoice.company_id,
                    invoice.date,
                ),
            )
            self.assertEqual(term_line.amount_discount_currency, -self.amount_discount)

    def test_customer_invoice_discount_term_line_multicurrency(self):
        """
        Test saving of discount on payment term line for multi currency customer
        invoice
        """
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            self.payment_term,
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        self.assertEqual(invoice.date, fields.Date.to_date("2019-04-01"))
        self.assertFalse(invoice.invoice_date)
        with freeze_time("2019-04-15"):
            invoice.action_post()
            self.assertEqual(invoice.date, fields.Date.to_date("2019-04-15"))
            self.assertEqual(invoice.invoice_date, fields.Date.to_date("2019-04-15"))
            self.assertTrue(invoice.has_discount_available)
            term_line = invoice.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type == "receivable"
            )
            self.assertEqual(term_line.date_discount, fields.Date.to_date("2019-04-25"))
            self.assertEqual(
                term_line.amount_discount,
                self.eur_currency._convert(
                    self.amount_discount,
                    self.usd_currency,
                    invoice.company_id,
                    invoice.date,
                ),
            )
            self.assertEqual(term_line.amount_discount_currency, self.amount_discount)

    def test_store_financial_discount_with_cash_rounding(self):
        five_cents_rounding = self.env["account.cash.rounding"].create(
            {
                "name": "5 cts rounding",
                "rounding": 0.05,
                "strategy": "biggest_tax",
                "rounding_method": "HALF-UP",
            }
        )
        self.init_invoice_line(self.invoice1, 1.0, 9.95)
        self.invoice1.invoice_cash_rounding_id = five_cents_rounding
        self.invoice1.action_post()
        payment_term_line = self.invoice1._get_first_payment_term_line()
        self.assertAlmostEqual(
            payment_term_line.amount_discount,
            -self.invoice1.amount_total * self.payment_term.percent_discount / 100,
            delta=0.01,
        )

    def test_single_invoice_payment_with_discount_available(self):
        """Test register payment for a vendor bill with available discount"""
        self.invoice1.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice1.ids,
                active_id=self.invoice1.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, False)
        self.assertEqual(payment_wizard_form.force_financial_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.invoice1.payment_state, ("paid", "in_payment"))

    def test_single_invoice_payment_with_discount_late_multicurrency(self):
        """Test register payment for a vendor bill with available discount"""
        invoice = self.init_invoice(
            self.partner,
            "in_invoice",
            self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        invoice.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=invoice.ids,
                active_id=invoice.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, True)
        self.assertEqual(payment_wizard_form.force_financial_discount, False)
        self.assertEqual(payment_wizard_form.currency_id, self.eur_currency)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard_form.force_financial_discount = True
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard_form.currency_id = self.usd_currency
        self.assertEqual(
            payment_wizard_form.amount,
            self.eur_currency._convert(
                self.amount_with_discount,
                self.usd_currency,
                invoice.company_id,
                payment_wizard_form.payment_date,
            ),
        )
        self.assertEqual(
            payment_wizard_form.payment_difference,
            self.eur_currency._convert(
                self.amount_discount,
                self.usd_currency,
                invoice.company_id,
                payment_wizard_form.payment_date,
            ),
        )
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))

    def test_single_invoice_payment_with_discount_late(self):
        """Test register payment for a vendor bill with late discount"""
        self.invoice2.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice2.ids,
                active_id=self.invoice2.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, True)
        self.assertEqual(payment_wizard_form.force_financial_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard_form.force_financial_discount = True
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))

    def test_single_invoice_payment_with_discount_late_forced(self):
        """Test register payment for a vendor bill with late discount forced"""
        self.invoice2.action_post()
        self.invoice2.force_financial_discount = True
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice2.ids,
                active_id=self.invoice2.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, True)
        # TODO: Check later on if we want to set this flag through default_get
        #  or _compute_from_lines (as ATM _compute_from_lines already depends
        #  on force_financial_discount to retrigger the computation when
        #  force_financial_discount is marked manually
        # self.assertEqual(payment_wizard_form.force_financial_discount, True)
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))

    def test_single_invoice_payment_without_discount(self):
        """Test register payment for a vendor bill without discount"""
        self.invoice3.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice3.ids,
                active_id=self.invoice3.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, False)
        self.assertEqual(payment_wizard_form.force_financial_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.invoice3.payment_state, ("paid", "in_payment"))

    @classmethod
    def _get_payment_lines(cls, invoice):
        """Returns payment lines match with the invoice"""
        # Inspired by account.move._get_reconciled_info_JSON_values
        invoice_term_lines = invoice.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type in ("receivable", "payable")
        )
        invoice_matched_lines = invoice_term_lines.mapped(
            "matched_debit_ids"
        ) | invoice_term_lines.mapped("matched_credit_ids")
        invoice_counterpart_lines = invoice_matched_lines.mapped(
            "debit_move_id"
        ) | invoice_matched_lines.mapped("debit_move_id")
        return invoice_counterpart_lines.filtered(
            lambda line: line not in invoice.line_ids
        )

    def test_multi_invoice_payment_with_discount_available(self):
        """Test register payment for multiple vendor bills with available discount"""
        invoice4 = self.invoice1.copy({"invoice_date": "2019-04-01"})
        self.assertTrue(invoice4.has_discount_available)
        invoices = self.invoice1 | invoice4
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertFalse(payment_wizard_form.show_force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(self.invoice1)
        self.assertIn(self.invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice4)
        self.assertIn(invoice4.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_payment_with_discount_available_grouped(self):
        """Test register payment grouped for multiple vendor bills with available discount"""
        invoice4 = self.invoice1.copy({"invoice_date": "2019-04-01"})
        self.assertTrue(invoice4.has_discount_available)
        invoices = self.invoice1 | invoice4
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertFalse(payment_wizard_form.show_force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard_form.group_payment = True
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount * 2)
        self.assertEqual(
            payment_wizard_form.payment_difference, self.amount_discount * 2
        )
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        invoice1_payment_line = self._get_payment_lines(self.invoice1)
        invoice4_payment_line = self._get_payment_lines(invoice4)
        self.assertEqual(invoice1_payment_line, invoice4_payment_line)
        # The payment move lines must have full amount to set invoices as paid
        self.assertEqual(
            invoice1_payment_line.amount_currency, self.amount_without_discount * 2
        )
        invoice_payment = invoice1_payment_line.mapped("payment_id")
        # The payment must have the amount with discount
        self.assertEqual(invoice_payment.amount, self.amount_with_discount * 2)
        for payment_line in invoice1_payment_line.move_id.line_ids:
            if payment_line == invoice1_payment_line:
                continue
            elif payment_line.account_id in (self.write_off_rev, self.write_off_exp):
                # Write off line must have the discount amount and label
                self.assertEqual(
                    payment_line.amount_currency, -self.amount_discount * 2
                )
                self.assertEqual(payment_line.name, "Financial Discount")
            else:
                # Oustanding payment line must have the amount with discount
                self.assertEqual(
                    payment_line.amount_currency, -self.amount_with_discount * 2
                )
        self.assertIn(self.invoice1.payment_state, ("paid", "in_payment"))
        self.assertIn(invoice4.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_payment_with_discount_late(self):
        """Test register payment for multiple vendor bills with late discount"""
        invoice4 = self.invoice2.copy({"invoice_date": self.invoice2.invoice_date})
        self.assertFalse(invoice4.has_discount_available)
        invoices = self.invoice2 | invoice4
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        invoice2_payment_line = self._get_payment_lines(self.invoice2)
        invoice2_payment = invoice2_payment_line.mapped("payment_id")
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))
        invoice4_payment_lines = self._get_payment_lines(invoice4)
        invoice4_payment = invoice4_payment_lines.mapped("payment_id")
        self.assertEqual(invoice4_payment.amount, self.amount_without_discount)
        self.assertIn(invoice4.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_payment_with_discount_late_forced(self):
        """Test register payment for multiple vendor bills with late discount forced
        at invoice level"""
        invoice4 = self.invoice2.copy({"invoice_date": self.invoice2.invoice_date})
        self.assertFalse(invoice4.has_discount_available)
        invoice4.force_financial_discount = True
        self.assertTrue(invoice4.has_discount_available)
        invoices = self.invoice2 | invoice4
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        invoice2_payment_lines = self._get_payment_lines(self.invoice2)
        invoice2_payment = invoice2_payment_lines.mapped("payment_id")
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice4)
        self.assertIn(invoice4.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_payment_with_discount_late_forced_wizard(self):
        """Test register payment grouped for multiple vendor bills with late discount
        forced at wizard level"""
        invoice4 = self.invoice2.copy({"invoice_date": self.invoice2.invoice_date})
        self.assertFalse(invoice4.has_discount_available)
        invoice4.force_financial_discount = True
        self.assertTrue(invoice4.has_discount_available)
        invoices = self.invoice2 | invoice4
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        payment_wizard_form.force_financial_discount = True
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(self.invoice2)
        self.assertIn(self.invoice2.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice4)
        self.assertIn(invoice4.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_eur_payment_eur_with_discount_available(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = invoice1.copy({"invoice_date": "2019-04-01"})
        self.assertTrue(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertFalse(payment_wizard_form.show_force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice2)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_eur_payment_eur_with_discount_available_grouped(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = invoice1.copy({"invoice_date": "2019-04-01"})
        self.assertTrue(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertFalse(payment_wizard_form.show_force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard_form.group_payment = True
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount * 2)
        self.assertEqual(
            payment_wizard_form.payment_difference, self.amount_discount * 2
        )
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        invoice1_payment_line = self._get_payment_lines(invoice1)
        invoice2_payment_line = self._get_payment_lines(invoice2)
        self.assertEqual(invoice1_payment_line, invoice2_payment_line)
        # The payment move lines must have full amount to set invoices as paid
        self.assertEqual(
            invoice2_payment_line.amount_currency, self.amount_without_discount * 2
        )
        invoice_payment = invoice1_payment_line.mapped("payment_id")
        # The payment must have the amount with discount
        self.assertEqual(invoice_payment.amount, self.amount_with_discount * 2)
        for payment_line in invoice1_payment_line.move_id.line_ids:
            if payment_line == invoice1_payment_line:
                continue
            elif payment_line.account_id in (self.write_off_rev, self.write_off_exp):
                # Write off line must have the discount amount and label
                self.assertEqual(
                    payment_line.amount_currency, -self.amount_discount * 2
                )
                self.assertEqual(payment_line.name, "Financial Discount")
            else:
                # Oustanding payment line must have the amount with discount
                self.assertEqual(
                    payment_line.amount_currency, -self.amount_with_discount * 2
                )
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_eur_payment_eur_with_discount_late(self):
        """Test register payment for multiple vendor bills with force discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        self.assertFalse(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        invoice2_payment_line = self._get_payment_lines(invoice2)
        invoice2_payment = invoice2_payment_line.mapped("payment_id")
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_eur_payment_eur_with_discount_late_forced(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        self.assertFalse(invoice2.has_discount_available)
        invoice2.force_financial_discount = True
        self.assertTrue(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice2)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_eur_payment_eur_with_discount_late_forced_wizard(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        self.assertFalse(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        payment_wizard_form.force_financial_discount = True
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice2)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_chf_payment_eur_with_discount_available(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.chf_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = invoice1.copy({"invoice_date": "2019-04-01"})
        self.assertTrue(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertFalse(payment_wizard_form.show_force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice2)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_chf_payment_eur_with_discount_available_grouped(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.chf_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = invoice1.copy({"invoice_date": "2019-04-01"})
        self.assertTrue(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertFalse(payment_wizard_form.show_force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard_form.group_payment = True
        self.assertEqual(payment_wizard_form.currency_id, self.eur_currency)
        amount_with_discount_chf_to_eur = self.chf_currency._convert(
            self.amount_with_discount * 2,
            self.eur_currency,
            invoice1.company_id,
            payment_wizard_form.payment_date,
        )
        amount_discount_chf_to_eur = self.chf_currency._convert(
            self.amount_discount * 2,
            self.eur_currency,
            invoice1.company_id,
            payment_wizard_form.payment_date,
        )
        self.assertAlmostEqual(
            payment_wizard_form.amount, amount_with_discount_chf_to_eur, delta=0.01
        )
        self.assertAlmostEqual(
            payment_wizard_form.payment_difference,
            amount_discount_chf_to_eur,
            delta=0.01,
        )
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        invoice1_payment_line = self._get_payment_lines(invoice1)
        invoice2_payment_line = self._get_payment_lines(invoice2)
        self.assertEqual(invoice1_payment_line, invoice2_payment_line)
        # The payment move lines must have full amount to set invoices as paid
        amount_without_discount_chf_to_eur = self.chf_currency._convert(
            self.amount_without_discount * 2,
            self.eur_currency,
            invoice1.company_id,
            payment_wizard_form.payment_date,
        )
        self.assertAlmostEqual(
            invoice2_payment_line.amount_currency,
            amount_without_discount_chf_to_eur,
            delta=0.01,
        )
        invoice_payment = invoice1_payment_line.mapped("payment_id")
        # The payment must have the amount with discount
        self.assertEqual(invoice_payment.amount, amount_with_discount_chf_to_eur)
        for payment_line in invoice1_payment_line.move_id.line_ids:
            if payment_line == invoice1_payment_line:
                continue
            elif payment_line.account_id in (self.write_off_rev, self.write_off_exp):
                # Write off line must have the discount amount and label
                self.assertEqual(
                    payment_line.amount_currency, -amount_discount_chf_to_eur
                )
                self.assertEqual(payment_line.name, "Financial Discount")
            else:
                # Oustanding payment line must have the amount with discount
                self.assertEqual(
                    payment_line.amount_currency, -amount_with_discount_chf_to_eur
                )
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_chf_payment_eur_with_discount_late(self):
        """Test register payment for multiple vendor bills with force discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.chf_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        self.assertFalse(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        invoice2_payment_line = self._get_payment_lines(invoice2)
        invoice2_payment = invoice2_payment_line.mapped("payment_id")
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_chf_payment_eur_with_discount_late_forced(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.chf_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.chf_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        self.assertFalse(invoice2.has_discount_available)
        invoice2.force_financial_discount = True
        self.assertTrue(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice2)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_multi_invoice_chf_payment_eur_with_discount_late_forced_wizard(self):
        """Test register payment for multiple vendor bills with discount"""
        invoice1 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
            currency=self.chf_currency,
        )
        self.init_invoice_line(invoice1, 1.0, 1000.0)
        self.assertTrue(invoice1.has_discount_available)
        invoice2 = self.init_invoice(
            self.partner,
            "in_invoice",
            payment_term=self.payment_term,
            invoice_date="2019-02-15",
            invoice_date_due="2019-03-15",
            currency=self.chf_currency,
        )
        self.init_invoice_line(invoice2, 1.0, 1000.0)
        self.assertFalse(invoice2.has_discount_available)
        invoices = invoice1 | invoice2
        invoices.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_ids=invoices.ids, active_model="account.move"
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        payment_wizard_form.force_financial_discount = True
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        payment_wizard_form.journal_id = self.eur_bank_journal
        self.assertFalse(payment_wizard_form.group_payment)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self._assert_payment_line_with_discount_from_invoice(invoice1)
        self.assertIn(invoice1.payment_state, ("paid", "in_payment"))
        self._assert_payment_line_with_discount_from_invoice(invoice2)
        self.assertIn(invoice2.payment_state, ("paid", "in_payment"))

    def test_customer_manual_payment_with_discount_available(self):
        """Test register payment for a customer invoice with available discount"""
        self.client_invoice1.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.client_invoice1.ids,
                active_id=self.client_invoice1.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, False)
        self.assertEqual(payment_wizard_form.force_financial_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_exp)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.client_invoice1.payment_state, ("paid", "in_payment"))

    def test_customer_manual_payment_with_discount_late(self):
        """Test register payment for a customer invoice with late discount"""
        self.client_invoice2.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.client_invoice2.ids,
                active_id=self.client_invoice2.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, True)
        self.assertEqual(payment_wizard_form.force_financial_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard_form.force_financial_discount = True
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_exp)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.client_invoice2.payment_state, ("paid", "in_payment"))

    def test_customer_manual_payment_with_discount_late_forced(self):
        """Test register payment for a customer invoice with late discount forced"""
        self.client_invoice2.action_post()
        self.client_invoice2.force_financial_discount = True
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.client_invoice2.ids,
                active_id=self.client_invoice2.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, True)
        # TODO: Check later on if we want to set this flag through default_get
        #  or _compute_from_lines (as ATM _compute_from_lines already depends
        #  on force_financial_discount to retrigger the computation when
        #  force_financial_discount is marked manually
        # self.assertEqual(payment_wizard_form.force_financial_discount, True)
        self.assertEqual(payment_wizard_form.amount, self.amount_with_discount)
        self.assertEqual(payment_wizard_form.payment_difference_handling, "reconcile")
        self.assertEqual(payment_wizard_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_wizard_form.writeoff_account_id, self.write_off_exp)
        self.assertEqual(payment_wizard_form.writeoff_label, "Financial Discount")
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.client_invoice2.payment_state, ("paid", "in_payment"))

    def test_customer_manual_payment_without_discount(self):
        """Test register payment for a customer invoice without discount"""
        self.client_invoice3.action_post()
        payment_wizard_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.client_invoice3.ids,
                active_id=self.client_invoice3.id,
            )
        )
        self.assertEqual(payment_wizard_form.show_force_financial_discount, False)
        self.assertEqual(payment_wizard_form.force_financial_discount, False)
        self.assertEqual(payment_wizard_form.amount, self.amount_without_discount)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.action_create_payments()
        self.assertIn(self.client_invoice3.payment_state, ("paid", "in_payment"))
