# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Payment Batch Transfer",
    "summary": "Add multi transfer in batch transfer",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/account-payment",
    "depends": ["account", "account_payment_fee_transfer"],
    "data": ["security/ir.model.access.csv", "views/account_payment_view.xml"],
    "installable": True,
    "maintainers": ["Saran440"],
}
