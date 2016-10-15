# -*- coding: utf-8 -*-
# Copyright 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class PaymentOrder(models.Model):
    _inherit = "payment.order"

    reference = fields.Char(
        string="Reference",
        states={
            "done": [
                ("readonly", True),
            ],
        },
        default="/",
        copy=False,
    )

    @api.model
    def create(self, values):
        result = super(PaymentOrder, self).create(values)

        obj_sequence = self.env["ir.sequence"]

        if result.mode.sequence_id:
            sequence = result.mode.sequence_id
            name = obj_sequence.next_by_id(sequence.id)
        else:
            name = obj_sequence.next_by_code("payment.order")

        result.write({"reference": name})
        return result
