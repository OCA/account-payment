# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Customer Early Payment Discount",
    "summary": "Early payment discount granted to customers settled by a credit note",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-payment",
    "author": "Jarsa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": ["account_early_payment_base"],
    "data": [
        "views/account_payment_term_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
