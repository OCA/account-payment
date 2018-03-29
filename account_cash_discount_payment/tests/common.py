# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account_cash_discount_base.tests.common import \
    TestAccountCashDiscountCommon


class TestAccountCashDiscountPaymentCommon(TestAccountCashDiscountCommon):

    @classmethod
    def setUpClass(cls):
        super(TestAccountCashDiscountPaymentCommon, cls).setUpClass()
        cls.PaymentLineCreate = cls.env['account.payment.line.create']
        cls.PaymentOrder = cls.env['account.payment.order']

        cls.payment_mode_out = cls.env.ref(
            'account_payment_mode.payment_mode_outbound_ct1')
        cls.bank_ing = cls.env.ref('base.bank_ing')
        cls.partner_bank_ing = cls.env.ref('base_iban.bank_iban_main_partner')

        cls.bank_ing_journal = cls.Journal.create({
            'name': 'ING Bank',
            'code': 'ING-B',
            'type': 'bank',
            'bank_id': cls.bank_ing.id,
        })

    def create_supplier_invoice(
            self, date, payment_mode, amount, discount_percent, tax_ids):
        invoice = self.AccountInvoice.create({
            'partner_id': self.partner_agrolait.id,
            'account_id': self.pay_account.id,
            'company_id': self.company.id,
            'journal_id': self.purchase_journal.id,
            'type': 'in_invoice',
            'date_invoice': date,
            'discount_due_date': date,
            'discount_percent': discount_percent,
            'payment_mode_id': payment_mode.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': "Test",
                    'quantity': 1,
                    'account_id': self.exp_account.id,
                    'price_unit': amount,
                    'invoice_line_tax_ids': [(6, 0, tax_ids)]
                })
            ]
        })
        invoice.compute_taxes()
        return invoice
