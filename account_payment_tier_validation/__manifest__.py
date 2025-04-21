# Copyright 2025 Spearhead - Ricardo Jara
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Payment Tier Validation",
    "summary": "Extends the functionality of Payment to "
    "support a tier validation process.",
    "version": "18.0.1.0.1",
    "category": "Generic Modules/Payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account", "base_tier_validation"],
    "data": ["views/account_payment_view.xml"],
}
