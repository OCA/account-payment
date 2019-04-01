# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Cash Discount Tax',
    'summary': """
        This module helps accoutant to fill in invoices with cash discount
        allowed on taxes only""",
    'version': '10.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-payment',
    'development_status': 'Alpha',
    'category': 'Accounting & Finance',
    'maintainers': ['rousseldenis'],
    'depends': [
        'account',
        'account_cash_discount_base',
    ],
    'data': [
        'views/account_config_settings.xml',
        'views/account_invoice.xml',
        'views/res_company.xml',
    ],
}
