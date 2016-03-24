# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{'name': 'Payment Order',
 'summary': 'Port of account_payment from v8',
 'version': '9.0.1.0.1',
 'author': "Odoo Community Association (OCA), brain-tec AG",
 'category': 'Accounting & Finance',
 'website': '',
 'license': 'AGPL-3',
 'depends': ['base','account', 'document','account_full_reconcile'],
 'data': [
        "wizard/account_payment_populate_statement_view.xml",
        "wizard/payment_order_create_view.xml",
        "views/payment_order_view.xml",
        "views/payment_line_view.xml",
        "payment_sequence.xml",
        'security/ir.model.access.csv',
          ],
 'auto_install': False,
 'installable': True,
 'images': []
 }
