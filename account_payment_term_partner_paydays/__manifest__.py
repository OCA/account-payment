# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Payment Term - Partner Payment Days",
    "version": "17.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": "Allows to define payment days for partners.",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "maintainer": "OCA",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "depends": ["account_payment_term_extension"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
