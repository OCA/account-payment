# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Payment Order',
    'summary': 'Port of account_payment from v8',
    'version': '9.0.1.0.1',
    'author': "Odoo Community Association (OCA), brain-tec AG",
    'category': 'Accounting & Finance',
    'website': 'https://github.com/OCA/bank-payment',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'account',
        'document',
        'account_full_reconcile',
        'base_iban',  # for manual_bank_transfer
        'account_full_reconcile',
    ],
    'data': [
        "data/payment_mode_type.xml",
        "wizard/account_payment_populate_statement_view.xml",
        "wizard/bank_payment_manual.xml",
        "wizard/payment_order_create_view.xml",
        "views/payment_order_view.xml",
        "views/payment_line_view.xml",
        "views/payment_mode.xml",
        "views/payment_mode_type.xml",
        "payment_sequence.xml",
        "security/ir.model.access.csv",
    ],
    'demo': [
        'demo/banking_demo.xml'
    ],
    'auto_install': False,
    'installable': True,
    'images': []
}
