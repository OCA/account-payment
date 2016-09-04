# -*- coding: utf-8 -*-
# © 2013 Agile Business Group sagl
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class VoucherLine(models.Model):

    _inherit = 'account.voucher.line'

    invoice_number = fields.Char(
        'Invoice Number',
        compute='_compute_invoice_number',
        size=64,
    )

    # @api.depends('move_line_id.invoice.document_number')
    def _compute_invoice_number(self):
        for line in self:
            if line.move_line_id:
                line.invoice_number = self.get_inv_num(
                    line.move_line_id.id)
            else:
                line.invoice_number = ''

    @api.model
    def get_inv_num(self, move_line_id):
        move_line = self.env['account.move.line'].browse(move_line_id)
        return (
            move_line.document_number or '')
