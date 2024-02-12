# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Register due payments",
    "summary": "Register only due payments",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Accounting/Payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["yajo", "rafaelbn"],
    "license": "LGPL-3",
    "application": False,
    "auto_install": False,
    "depends": ["account"],
    "data": [
        "views/account_move_line_view.xml",
    ],
}
