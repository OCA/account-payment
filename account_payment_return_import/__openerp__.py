# -*- coding: utf-8 -*-
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Payment Return Import',
    'category': 'Accounting',
    'version': '8.0.1.0.0',
    'summary': 'This module add a generic wizard to import payment return file'
               'formats. Is only the base to be extended by another modules',
    'license': 'AGPL-3',
    'author': 'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'https://www.tecnativa.com',
    'depends': ['account_payment_return'],
    'data': [
        'wizard/payment_return_import_view.xml',
    ],
    'installable': True,
}
