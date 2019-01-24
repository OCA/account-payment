# Copyright 2011-2012 7 i TRIA <http://www.7itria.cat>
# Copyright 2011-2012 Avanzosc <http://www.avanzosc.com>
# Copyright 2013 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2014 Markus Schneider <markus.schneider@initos.com>
# Copyright 2015 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2015-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Returns",
    "version": "12.0.1.0.0",
    "summary": "Manage the return of your payments",
    'license': 'AGPL-3',
    "depends": [
        'mail',
        'account',
    ],
    'author': 'Odoo Community Association (OCA),'
              '7 i TRIA, '
              'Tecnativa, '
              'initOS GmbH & Co., ',
    'website': 'https://github.com/OCA/account-payment',
    'data': [
        'security/ir.model.access.csv',
        'security/account_payment_return_security.xml',
        'views/payment_return_view.xml',
        'views/account_journal_view.xml',
        'data/ir_sequence_data.xml',
        'views/account_invoice_view.xml',
    ],
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
    'installable': True,
}
