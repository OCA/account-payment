# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class TestAccountCashDiscountTax(common.SavepointCase):

    def setUp(self):
        super(TestAccountCashDiscountTax, self).setUp()
        self.partner_agrolait = self.env.ref('base.res_partner_2')
        self.invoice_obj = self.env['account.invoice']
        self.payment_term_obj = self.env['account.payment.term']

        vals = {
            'name': '3% cash discount on 15 days',
            'discount_percent': 3.0,
            'discount_delay': 15,
            'line_ids': [(0, 0, {
                'value': 'balance',
                'days': 15,
                'option': 'day_after_invoice_date',
            })]
        }
        self.term_15_3 = self.payment_term_obj.create(vals)

        vals = {
            'name': 'TAX 20',
            'amount': 20.0,
        }
        self.tax_20 = self.env['account.tax'].create(vals)

        vals = {
            'name': 'TAX 6',
            'amount': 6.0,
        }
        self.tax_6 = self.env['account.tax'].create(vals)

        # Create a group of taxes
        vals = {
            'name': 'GROUP 20 - 6',
            'amount_type': 'group',
            'amount': 1,
            'children_tax_ids': [(6, 0, [self.tax_20.id, self.tax_6.id])]
        }
        self.tax_20_6 = self.env['account.tax'].create(vals)

        vals = {
            'name': 'Receivable',
            'code': 'RCV',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id
        }
        self.recv_account = self.env['account.account'].create(vals)
        vals = {
            'name': 'Payable',
            'code': 'PAY',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_payable').id
        }
        account_pay = self.env['account.account'].create(vals)
        vals = {
            'name': 'Expenses',
            'code': 'EXP',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_expenses').id
        }
        self.exp_account = self.env['account.account'].create(vals)
        vals = {
            'name': 'Discount',
            'code': 'DISC',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_expenses').id
        }
        self.purchase_journal = self.env['account.journal'].create({
            'name': 'Purchases Test',
            'code': 'PJ-T',
            'type': 'purchase',
        })
        self.disc_account = self.env['account.account'].create(vals)
        self.env.user.company_id.partner_id.property_account_receivable_id = \
            self.recv_account
        self.env.user.company_id.partner_id.property_account_payable_id = \
            account_pay
        self.partner_agrolait.property_account_receivable_id =\
            self.recv_account
        self.partner_agrolait.property_account_payable_id = account_pay
        self.env.user.company_id.cash_discount_tax_description = \
            'The Discount'
        self.env.user.company_id.enable_cash_discount_tax = True

    def _create_invoice(self, amount, tax=None):
        self.invoice = self.invoice_obj.create({
            'partner_id': self.partner_agrolait.id,
            'account_id': self.recv_account.id,
            'company_id': self.env.user.company_id.id,
            'journal_id': self.purchase_journal.id,
            'type': 'in_invoice',
            'invoice_line_ids': [
                (0, 0, {
                    'name': "Test",
                    'quantity': 1,
                    'account_id': self.exp_account.id,
                    'price_unit': amount,
                    'invoice_line_tax_ids': [
                        (6, 0, [tax and tax.id or self.tax_20.id])],
                })
            ]
        })
        self.invoice.compute_taxes()
        return self.invoice

    def _create_invoice_taxes(self, amount):
        self.invoice = self.invoice_obj.create({
            'partner_id': self.partner_agrolait.id,
            'account_id': self.recv_account.id,
            'company_id': self.env.user.company_id.id,
            'journal_id': self.purchase_journal.id,
            'type': 'in_invoice',
            'invoice_line_ids': [
                (0, 0, {
                    'name': "Test 20",
                    'quantity': 1,
                    'account_id': self.exp_account.id,
                    'price_unit': amount,
                    'invoice_line_tax_ids': [(6, 0, [self.tax_20.id])],
                }),
                (0, 0, {
                    'name': "Test 6",
                    'quantity': 3,
                    'account_id': self.exp_account.id,
                    'price_unit': amount,
                    'invoice_line_tax_ids': [(6, 0, [self.tax_6.id])],
                })
            ]
        })
        self.invoice.compute_taxes()
        return self.invoice

    def test_invoice(self):
        # Create invoice
        # Check that taxes are == 200.0
        # Launch Wizard to add tax cash discount lines
        # Check new lines values
        # Check tax amount (tax amount == (200.0 - (200.0 * 3 %))
        self.env.user.company_id.cash_discount_tax_account_id = \
            self.disc_account
        self.env.user.company_id.cash_discount_base_amount_type = 'untaxed'
        self.partner_agrolait.property_supplier_payment_term_id =\
            self.term_15_3
        self._create_invoice(1000.0)
        self.invoice._onchange_payment_term_discount_options()
        self.assertEquals(
            1,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            200.0,
            self.invoice.amount_tax,
        )
        self.invoice.action_add_cash_discount_tax_lines()

        self.assertEquals(
            3,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            ['The Discount', 'The Discount'],
            self.invoice.invoice_line_ids.filtered(
                'is_cash_discount_tax').mapped('name'),
        )
        self.assertEquals(
            194.0,
            self.invoice.amount_tax,
        )
        # Base amount remains
        self.assertEquals(
            1000.0,
            self.invoice.amount_untaxed,
        )

    def test_invoice_group(self):
        # Create invoice
        # Check that taxes are == 260.0
        # Launch Wizard to add tax cash discount lines
        # Check new lines values
        # Check tax amount (tax amount == (260.0 - (260.0 * 3 %))
        self.env.user.company_id.cash_discount_tax_account_id = \
            self.disc_account
        self.env.user.company_id.cash_discount_base_amount_type = 'untaxed'
        self.partner_agrolait.property_supplier_payment_term_id =\
            self.term_15_3
        self._create_invoice(1000.0, self.tax_20_6)
        self.invoice._onchange_payment_term_discount_options()
        self.assertEquals(
            1,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            260.0,
            self.invoice.amount_tax,
        )
        self.invoice.action_add_cash_discount_tax_lines()

        self.assertEquals(
            3,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            ['The Discount', 'The Discount'],
            self.invoice.invoice_line_ids.filtered(
                'is_cash_discount_tax').mapped('name'),
        )
        compare = float_compare(252.20, self.invoice.amount_tax, 2)
        self.assertEqual(
            0,
            compare,
        )
        # Base amount remains
        self.assertEquals(
            1000.0,
            self.invoice.amount_untaxed,
        )

    def test_invoice_no_group(self):
        # Create invoice
        # Check that taxes are == 260.0
        # Launch Wizard to add tax cash discount lines
        # Check new lines values
        # Check tax amount (tax amount == (260.0 - (260.0 * 3 %))
        self.env.user.company_id.cash_discount_invoice_tax = True
        self.env.user.company_id.cash_discount_tax_account_id = \
            self.disc_account
        self.env.user.company_id.cash_discount_base_amount_type = 'untaxed'
        self.partner_agrolait.property_supplier_payment_term_id = \
            self.term_15_3
        self._create_invoice(1000.0, self.tax_20_6)
        self.invoice._onchange_payment_term_discount_options()
        self.assertEquals(
            1,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            260.0,
            self.invoice.amount_tax,
        )
        self.invoice.action_add_cash_discount_tax_lines()

        self.assertEquals(
            5,
            len(self.invoice.invoice_line_ids),
        )

        compare = float_compare(252.20, self.invoice.amount_tax, 2)
        self.assertEqual(
            0,
            compare,
        )
        # Base amount remains
        self.assertEquals(
            1000.0,
            self.invoice.amount_untaxed,
        )

    def test_invoice_taxes(self):
        # Create invoice with several taxes
        # Check that taxes are == 380.0 (1000.0 * 20%) + (3000.0 * 6%)
        # Launch Wizard to add tax cash discount lines
        # Check new lines values
        # Check tax amount (tax amount == (380.0 - (380.0 * 3 %))
        self.env.user.company_id.cash_discount_tax_account_id = \
            self.disc_account
        self.env.user.company_id.cash_discount_base_amount_type = 'untaxed'
        self.partner_agrolait.property_supplier_payment_term_id =\
            self.term_15_3
        self._create_invoice_taxes(1000.0)
        self.invoice._onchange_payment_term_discount_options()
        self.assertEquals(
            2,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            380.0,
            self.invoice.amount_tax,
        )
        self.invoice.action_add_cash_discount_tax_lines()
        # Invoices Lines (2) + (2 * cash discount lines - 2 per tax)
        self.assertEquals(
            6,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            ['The Discount', 'The Discount', 'The Discount', 'The Discount'],
            self.invoice.invoice_line_ids.filtered(
                'is_cash_discount_tax').mapped('name'),
        )
        self.assertEquals(
            368.60,
            self.invoice.amount_tax,
        )
        # Base amount remains
        self.assertEquals(
            4000.0,
            self.invoice.amount_untaxed,
        )

    def test_invoice_draft(self):
        # Create invoice and Validate
        # Launch Wizard to add tax cash discount lines
        # Check error raises
        self.env.user.company_id.cash_discount_tax_account_id = \
            self.disc_account
        self.env.user.company_id.cash_discount_base_amount_type = 'untaxed'
        self.partner_agrolait.property_supplier_payment_term_id =\
            self.term_15_3
        self._create_invoice(1000.0)
        self.invoice._onchange_payment_term_discount_options()
        self.assertEquals(
            1,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            200.0,
            self.invoice.amount_tax,
        )
        self.invoice.action_invoice_open()
        with self.assertRaises(ValidationError):
            self.invoice.action_add_cash_discount_tax_lines()

    def test_invoice_taxes_disabled(self):
        # Create invoice with several taxes
        # Check that taxes are == 380.0 (1000.0 * 20%) + (3000.0 * 6%)
        # Launch Wizard to add tax cash discount lines
        # Check new lines values
        # Check tax amount (tax amount == (380.0 - (380.0 * 3 %))
        self.env.user.company_id.enable_cash_discount_tax = False
        self.env.user.company_id.cash_discount_tax_account_id = \
            self.disc_account
        self.env.user.company_id.cash_discount_base_amount_type = 'untaxed'
        self.partner_agrolait.property_supplier_payment_term_id =\
            self.term_15_3
        self._create_invoice_taxes(1000.0)
        self.invoice._onchange_payment_term_discount_options()
        self.assertEquals(
            2,
            len(self.invoice.invoice_line_ids),
        )
        self.assertEquals(
            380.0,
            self.invoice.amount_tax,
        )
        with self.assertRaises(ValidationError):
            self.invoice.action_add_cash_discount_tax_lines()
