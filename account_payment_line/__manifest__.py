# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Payment Counterpart Lines",
    "summary": """Payment Counterpart Lines""",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "category": "Account",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_payment_views.xml",
    ],
    "maintainers": ["ChrisOForgeFlow"],
    "installable": True,
    "post_load": "post_load_hook",
    "auto_install": False,
}
