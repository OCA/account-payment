# Copyright 2025 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Payment Show Invoice",
    "summary": "Extends the tree view of payments to show the paid invoices "
    "related to the payments using the vendor reference by default",
    "version": "18.0.1.0.0",
    "category": "Account-payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account"],
    "data": ["views/account_payment_view.xml"],
}
