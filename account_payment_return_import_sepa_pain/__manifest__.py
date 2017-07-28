# -*- coding: utf-8 -*-
# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Payment Return Import SEPA Pain',
    'category': 'Accounting',
    'version': '10.0.1.0.0',
    'summary': 'Module to import SEPA Direct Debit Unpaid Report File Format '
               'PAIN.002.001.03',
    'license': 'AGPL-3',
    'author': 'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'https://www.tecnativa.com',
    'depends': [
        'account_payment_return_import',
        'account_payment_order',
    ],
    'data': [
        'data/unpaid_reason_codes.xml'
    ],
    'installable': True,
}
