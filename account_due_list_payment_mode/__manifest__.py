# -*- coding: utf-8 -*-

{
    "name": "Payment due list with payment mode",
    "version": "11.0.1.0.0",
    "category": "Generic Modules/Payment",
    "author": "Obertix Free Solutions, "
              "Tecnativa, "
              "Odoo Community Association (OCA),",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-payment",
    "depends": [
        "account_payment_partner",
        "account_due_list",
    ],
    "data": [
        'views/payment_view.xml',
    ],
    "application": False,
    "installable": True,
}
