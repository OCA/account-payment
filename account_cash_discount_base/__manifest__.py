# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Cash Discount Base',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/acsone/account-payment',
    'category': 'Accounting',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_invoice.xml',
        'views/account_payment_term.xml',
        'views/res_company.xml',
        'reports/report_invoice.xml',
    ],
}
