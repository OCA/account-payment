# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': "Payments Due list aging comments",
    'version': '9.0.0.1.0',
    'category': 'Generic Modules/Payment',
    'author': 'Eficent,'
              'Odoo Community Association (OCA)',
    'website': 'http://www.eficent.com',
    'license': 'AGPL-3',
    "depends": [
        'account_due_list',
        'account_accountant',
    ],
    "data": [
        'views/payment_view.xml',
    ],
    "installable": True,
}
