# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Cash Discount Base Purchase',
    'summary': """
        Makes the glue between account_cash_dicount_base module behaviour and
        purchase module""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'development_status': 'Beta',
    'maintainers': ['rousseldenis'],
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-payment',
    'depends': [
        'account_cash_discount_base',
        'purchase',
    ],
    'auto_install': True,
}
