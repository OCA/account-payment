# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Early Payment Discount Base",
    "summary": "Common ground of the early payment discounts settled by a credit note",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-payment",
    "author": "Jarsa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": ["account", "resource"],
    "data": [
        "views/account_move_views.xml",
    ],
    "installable": True,
}
