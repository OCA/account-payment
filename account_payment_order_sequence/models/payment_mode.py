# -*- coding: utf-8 -*-
# Copyright 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    sequence_id = fields.Many2one(
        string="Sequence",
        comodel_name="ir.sequence",
    )
