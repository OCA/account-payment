# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Payment Term Security",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainer": "OCA",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "depends": ["account_payment_term_security", "sale"],
    "data": [
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "maintainers": ["victoralmau"],
}
