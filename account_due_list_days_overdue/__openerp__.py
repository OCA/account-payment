# -*- coding: utf-8 -*-
# © 2016 Eficent Business and IT Consulting Services S.L. (
# <http://www.eficent.com>).
# © 2016 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': "Payments Due list days overdue",
    'version': '8.0.0.1.0',
    'category': 'Accounting',
    'author': 'Odoo Community Association (OCA), '
              'Eficent Business and IT Consulting Services S.L., ',
    'website': 'http://www.eficent.com',
    'license': 'AGPL-3',
    "depends": [
        'account_due_list',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/account_overdue_term_view.xml',
        'views/account_move_line_view.xml'
    ],
    "demo": [
        'demo/account_overdue_term_demo.xml'
    ],
    "installable": True,
}
