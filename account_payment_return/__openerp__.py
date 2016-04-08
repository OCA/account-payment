# -*- coding: utf-8 -*-
# © 2011-2012 7 i TRIA <http://www.7itria.cat>
# © 2011-2012 Avanzosc <http://www.avanzosc.com>
# © 2013 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# © 2014 Markus Schneider <markus.schneider@initos.com>
# © 2015 Sergio Teruel <sergio.teruel@tecnativa.com>
# © 2015 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Returns",
    "version": "8.0.1.0.0",
    "summary": "Manage the return of your payments",
    'license': 'AGPL-3',
    "depends": [
        'mail',
        'account',
    ],
    'author': '7 i TRIA, '
              'Tecnativa, '
              'initOS GmbH & Co., '
              'Odoo Community Association (OCA)',
    'website': 'http://www.tecnativa.com',
    'data': [
        'security/ir.model.access.csv',
        'security/account_payment_return_security.xml',
        'views/payment_return_view.xml',
        'data/ir_sequence_data.xml',
        'views/account_invoice_view.xml',
    ],
    'installable': True,
}
