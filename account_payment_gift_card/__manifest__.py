# Copyright 2021 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "account_payment_gift_card",
    "summary": "Account Payment gift card",
    "version": "14.0.1.0.0",
    "category": "Accounting/Payment Acquirers",
    "website": "https://github.com/OCA/account-payment",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["Kev-Roche"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "gift_card",
        "payment",
    ],
    "data": [
        "data/data.xml",
    ],
}
