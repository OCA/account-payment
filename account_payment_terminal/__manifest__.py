# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Terminal",
    "summary": """This addon allows to pay invoices using payment terminal""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": ["sbejaoui"],
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account"],
    "data": [
        "security/account_payment_terminal.xml",
        "views/account_payment_terminal_views.xml",
        "views/account_journal_views.xml",
        "views/oca_payment_terminal_form_mixin.xml",
        "wizards/account_payment_register.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_payment_terminal/static/src/js/views/"
            "payment_terminal_form/payment_terminal_form_controller.js",
            "account_payment_terminal/static/src/js/views/"
            "payment_terminal_form/payment_terminal_form_view.js",
        ],
    },
}
