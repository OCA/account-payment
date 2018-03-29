# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Cash Discount Payment',
    'version': '10.0.1.0.0',
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/acsone/account-payment',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'depends': [
        'account_cash_discount_base',
        'account_payment_order',
    ],
    'data': [
        'views/account_move_line.xml',
        'views/account_payment_line.xml',
        'wizards/account_payment_line_create.xml',
    ],
    'demo': [],
}
