# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Terminal",
    "summary": """This addon allows to pay invoices using payment terminal""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": ["sbejaoui"],
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account"],
    "data": [
        "security/account_payment_terminal.xml",
        "views/webclient_templates.xml",
        "views/account_payment_terminal.xml",
        "views/account_journal.xml",
        "views/oca_payment_terminal_form_mixin.xml",
        "wizards/account_payment_register.xml",
    ],
}
