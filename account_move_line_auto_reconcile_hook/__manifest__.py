# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Move Line Auto Reconcile Hook",
    "summary": "Adds Hook to account move line",
    "version": "12.0.1.0.0",
    "category": "Account-payment",
    "website": "https://github.com/OCA/account-payment",
    "author": "Eficent, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account"],
    'post_load': 'post_load_hook',
}
