# Copyright 2019 Lorenzo Battistini
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Outbound payments: select account",
    "summary": "Allow user to select the account where journal item will be recorded",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Invoicing Management",
    "website": "https://github.com/OCA/account-payment",
    "author": "TAKOBI, Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "views/account_payment_view.xml"
    ],
}
