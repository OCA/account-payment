# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""This module contains a single "wizard" for confirming manual
bank transfers.
"""

from openerp import models, api


class PaymentManual(models.TransientModel):
    _name = 'payment.manual'
    _description = 'Send payment order(s) manually'

    @api.multi
    def button_ok(self):
        for order_id in self.env.context.get('active_ids', []):
            self.env['payment.order'].browse(order_id).action_done()
        return {'type': 'ir.actions.act_window_close'}
