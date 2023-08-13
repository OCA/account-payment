# Copyright <2023> ArcheTI <info@archeti.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Account Payment Tier Validation",
    "summary": "Extends the functionality of Payments to "
    "support a tier validation process.",
    "version": "16.0.1.0.0",
    "category": "Accounts",
    "website": "https://github.com/OCA/account-payment",
    "author": "ArcheTI, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account", "base_tier_validation"],
    "data": ["views/account_payment_views.xml"],
}
