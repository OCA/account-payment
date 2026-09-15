# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Supplier Early Payment Discount",
    "summary": "Early payment discount of the supplier settled by a credit note",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-payment",
    "author": "Jarsa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": ["account_early_payment_base", "purchase_stock", "mail_activity_team"],
    "data": [
        "security/account_move_security.xml",
        "data/mail_activity_team_data.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
