# Copyright 2023 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Due List Payment",
    "summary": """
        Allows you to make payments directly from the due list view""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Engenere.one,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "depends": [
        "account_due_list",
    ],
    "data": [
        "views/account_move_line.xml",
    ],
    "demo": [],
}
