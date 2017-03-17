# -*- coding: utf-8 -*-
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from openerp import api, models


class PaymentReturnLine(models.Model):
    _inherit = "payment.return.line"

    @api.multi
    def _find_match(self):
        lines = self.filtered(lambda x: not x.move_line_ids and x.reference)
        for line in lines:
            ref_pattern = line.return_id.journal_id.payment_return_pattern
            find_ref = False
            if ref_pattern:
                find_ref = re.findall(ref_pattern, line.reference)
            reference = find_ref and find_ref[0] or line.reference
            bank_payment_line = self.env['bank.payment.line'].search(
                [('name', '=', reference)])
            if bank_payment_line:
                line.move_line_ids = bank_payment_line.transit_move_line_id.ids
        super(PaymentReturnLine, lines)._find_match()
