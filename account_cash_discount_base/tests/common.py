# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestAccountCashDiscountCommon(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountCashDiscountCommon, cls).setUpClass()
        cls.Account = cls.env['account.account']
        cls.AccountInvoice = cls.env['account.invoice']
        cls.AccountInvoiceRefund = cls.env['account.invoice.refund']
        cls.AccountMoveLine = cls.env['account.move.line']
        cls.Journal = cls.env['account.journal']
        cls.MoveLine = cls.env['account.move.line']
        cls.Tax = cls.env['account.tax']

        cls.company = cls.env.ref('base.main_company')
        cls.partner_agrolait = cls.env.ref('base.res_partner_2')

        cls.recv_account_type = cls.env.ref(
            'account.data_account_type_receivable')
        cls.pay_account_type = cls.env.ref(
            'account.data_account_type_payable')
        cls.exp_account_type = cls.env.ref(
            'account.data_account_type_expenses')
        cls.inc_account_type = cls.env.ref(
            'account.data_account_type_other_income')

        cls.recv_account = cls.Account.search([
            ('user_type_id', '=', cls.recv_account_type.id)
        ], limit=1)
        cls.pay_account = cls.Account.search([
            ('user_type_id', '=', cls.pay_account_type.id)
        ], limit=1)
        cls.exp_account = cls.Account.search([
            ('user_type_id', '=', cls.exp_account_type.id)
        ], limit=1)

        cls.tax_10_p = cls.Tax.create({
            'sequence': 30,
            'name': 'Tax 10.0% (Percentage of Price)',
            'amount': 10.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
        })

        cls.tax_15_p = cls.Tax.create({
            'sequence': 30,
            'name': 'Tax 15.0% (Percentage of Price)',
            'amount': 15.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
        })

        cls.tax_17_p = cls.Tax.create({
            'sequence': 30,
            'name': 'Tax 17.0% (Percentage of Price)',
            'amount': 17.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
        })

        cls.sales_journal = cls.Journal.create({
            'name': 'Sales Test',
            'code': 'SJ-T',
            'type': 'sale',
        })

        cls.purchase_journal = cls.Journal.create({
            'name': 'Purchases Test',
            'code': 'PJ-T',
            'type': 'purchase',
        })

        cls.payment_term = cls.env.ref('account.account_payment_term')
