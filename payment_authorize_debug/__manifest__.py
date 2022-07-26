# Copyright (C) 2022, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payment Authorize Debug",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "summary": """
        This module allows you to activate debug information when contacting Authorize.net.
    """,
    "category": "Extra",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["payment_authorize"],
    "data": ["views/payment_acquirer.xml", "views/payment_transaction.xml"],
    "installable": True,
}
