# Copyright 2026 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Payment Term Installment",
    "summary": """
        Generate payment term lines automatically from a desired number of
        installments.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "category": "Accounting & Finance",
    "depends": ["account"],
    "data": [
        "views/account_payment_term_view.xml",
    ],
    "installable": True,
    "application": False,
    "maintainers": ["kaynnan"],
}
