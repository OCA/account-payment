# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, models


class PaymentOrderCreate(models.TransientModel):

    _inherit = 'payment.order.create'

    @api.multi
    def search_entries(self):
        result = super(PaymentOrderCreate, self).search_entries()
        line_obj = self.env['account.move.line']
        result.get('context', {}).update({'line_ids': line_obj.search(
            [('id', 'in', result['context']['line_ids']),
             ('under_payment', '=', False)]).ids})
        return result
