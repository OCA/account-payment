# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, fields, api


class PaymentLine(models.Model):
    _inherit = "payment.line"

    failed = fields.Boolean(
        string="Failed",
        default=False,
        copy=False)

    @api.multi
    def set_failed(self):
        self.failed = not self.failed
        return True
