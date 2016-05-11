# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    Copyright (C) 2016 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
