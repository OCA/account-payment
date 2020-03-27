# Copyright 2019 ACSONE SA/NV (<https://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentReturn(models.Model):
    _inherit = "payment.return"

    imported_bank_account_id = fields.Many2one(
        string="Bank account",
        help="Bank account from the imported file",
        comodel_name="res.partner.bank",
        ondelete="restrict",
        readonly=True,
    )
