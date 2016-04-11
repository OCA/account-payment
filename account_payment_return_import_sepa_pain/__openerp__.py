# -*- coding: utf-8 -*-
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Payment Return Import SEPA Pain',
    'category': 'Accounting',
    'version': '8.0.1.0.0',
    'summary': 'Module to import SEPA Direct Debit Unpaid Report File Format '
               'PAIN.002.001.03',
    'license': 'AGPL-3',
    'author': 'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'https://www.tecnativa.com',
    'depends': [
        'account_payment_return_import',
        'account_banking_payment_export',
    ],
    'data': [
        'data/unpaid_reason_codes.xml'
    ],
    'installable': True,
}
