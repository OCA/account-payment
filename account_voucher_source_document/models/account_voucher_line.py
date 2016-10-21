# -*- coding: utf-8 -*-
# © 2013 Agile Business Group sagl
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class account_voucher_line(models.Model):
    _inherit = 'account.voucher.line'

    @api.model
    def get_document_source(self, move_line_id):
        move_line = self.env['account.move.line'].browse(move_line_id)
        return move_line.invoice and move_line.invoice.origin or ''

    @api.depends('move_line_id.invoice.origin')
    def _compute_document_source(self):
        for line in self:
            move_line = line.move_line_id
            if move_line:
                line.document_source = self.get_document_source(move_line.id)
            else:
                line.document_source = ''

    document_source = fields.Char(
        'Document source',
        compute='_compute_document_source',
        size=64,
        store=True,
    )
