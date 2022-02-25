# Copyright 2021 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Gift Card Invoice Refund",
    "summary": "account gift card invoice refund",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-payment",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["Kev-Roche"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
        "gift_card",
    ],
    "data": [
        "data/data.xml",
        "views/account_move.xml",
        "views/gift_card.xml",
        "wizards/account_move_reversal.xml",
    ],
}
