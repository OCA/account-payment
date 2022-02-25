# Copyright (C) 2021 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GiftCardCustomize(models.Model):
    _inherit = "gift.card"

    invoice_id = fields.Many2one(comodel_name="account.move", string=" Refund Invoice")
