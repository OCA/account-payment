# -*- coding: utf-8 -*-

{
    "name": "Payment due list with payment mode",
    "version": "9.0.1.0.0",
    "category": "Generic Modules/Payment",
    "author": "Obertix Free Solutions, "
              "Tecnativa, "
              "Odoo Community Association (OCA),",
    "website": "https://odoo-community.org/",
    "depends": [
        "account_payment_partner",
        "account_due_list",
    ],
    "data": [
        'views/payment_view.xml',
    ],
    'installable': True,
    "auto_install": True,
    'license': 'AGPL-3',
}
