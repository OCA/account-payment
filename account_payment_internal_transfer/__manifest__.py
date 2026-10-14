# Copyright 2026 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Account Payment Internal Transfer",
    "summary": "Restore internal transfer functionality between bank/cash journals",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting/Accounting",
    "website": "https://github.com/OCA/account-payment",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "views/account_journal_dashboard_view.xml",
        "views/account_payment_views.xml",
    ],
}
