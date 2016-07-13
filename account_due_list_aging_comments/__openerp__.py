# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': "Payments Due list aging comments",
    'version': '8.0.0.2.0',
    'category': 'Generic Modules/Payment',
    'author': 'Odoo Community Association (OCA), '
              'Eficent Business and IT Consulting Services S.L., ',
    'website': 'http://www.eficent.com',
    'license': 'AGPL-3',
    "depends": [
        'account_due_list',
    ],
    "data": [
        'views/payment_view.xml',
    ],
    "installable": True,
}
