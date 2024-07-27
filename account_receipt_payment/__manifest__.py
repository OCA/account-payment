# Copyright 2024 Sergio Zanchetta (Associazione PNLUG - Gruppo Odoo)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Receipt Payment in Portal",
    "version": "14.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": "Enable payment of receipts in Portal",
    "author": "Pordenone Linux User Group (PNLUG), Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-payment",
    "license": "AGPL-3",
    "depends": ["account_payment", "account_receipt_portal"],
    "data": [
        "views/account_portal_templates.xml",
    ],
    "installable": True,
    "auto_install": True,
}
