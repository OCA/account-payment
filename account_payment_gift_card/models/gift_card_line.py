# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GiftCardLine(models.Model):
    _inherit = "gift.card.line"

    transaction_id = fields.Many2one("payment.transaction", string="Transaction")
