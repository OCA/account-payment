# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from odoo.addons import decimal_precision as dp


class Partner(models.Model):
    _inherit = "res.partner"

    # TODO: Calculate this, but do not auto-compute this out of performance
    # considerations.
    customer_wallet_balance = fields.Float(
        string="Customer Wallet Balance",
        digits=dp.get_precision("Product Price"),
        readonly=True,
        default=0,
    )
