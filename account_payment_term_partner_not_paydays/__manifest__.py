# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Payment Term - Partner Not Payment Days",
    "version": "17.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": """
        Recalculate the due date based on the non-payment
        days configured per contact.
    """,
    "author": "Binhex,Odoo Community Association (OCA)",
    "maintainer": "OCA",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "depends": ["account_payment_term_partner_paydays"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/account_payment_term_views.xml",
        "views/account_move_views.xml",
        "wizards/res_config_settings_view.xml",
    ],
    "installable": True,
}
