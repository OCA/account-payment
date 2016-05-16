# -*- coding: utf-8 -*-
# © 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
# © 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{
    'name': 'VAT on payment',
    'version': '8.0.1.0.0',
    'category': 'Generic Modules/Accounting',
    'depends': ['account_voucher_cash_basis'],
    'author': 'Agile Business Group, '
              'Odoo Community Association (OCA)',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    'summary': 'VAT on Payment',
    'data': [
        'account_account_view.xml',
        'account_tax_code_view.xml',
        'account_journal_view.xml',
        'account_invoice_view.xml',
        'account_move_line_view.xml',
        'account_voucher_view.xml',
        'account_config_settings_view.xml',
        'account_fiscal_position_view.xml',
    ],
    'demo': [
        'account_demo.xml',
    ],
    'test': [
        'test/account_invoice_1.yml',
        'test/account_invoice_2.yml',
        'test/account_invoice_3.yml',
        'test/account_invoice_4.yml',
        'test/account_invoice_5.yml',
        'test/account_invoice_6.yml',
        'test/account_invoice_7.yml',
        'test/account_invoice_8.yml',
        'test/account_invoice_9.yml',
        'test/account_invoice_1_real.yml',
        'test/account_invoice_2_real.yml',
        'test/account_invoice_3_real.yml',
        'test/account_invoice_4_real.yml',
        'test/account_invoice_5_real.yml',
        'test/account_invoice_6_real.yml',
        'test/account_invoice_7_real.yml',
        'test/account_invoice_8_real.yml',
        'test/account_invoice_1_real_same_account.yml',
        'test/account_invoice_1_bank.yml',
        'test/account_invoice_2_bank.yml',
        'test/account_invoice_3_bank.yml',
        'test/account_invoice_5_bank.yml',
        'test/account_invoice_1_bank_shadow.yml',
        'test/account_invoice_4_bank_shadow.yml',
        'test/account_invoice_6_bank_shadow.yml',
    ],
    'images': [],
    'installable': True,
}
