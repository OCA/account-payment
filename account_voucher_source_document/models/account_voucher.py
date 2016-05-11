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

from openerp import api, models


class account_voucher(models.Model):

    _inherit = 'account.voucher'

    @api.model
    def _get_source(self, res, line_type):
        line_obj = self.env['account.voucher.line']
        value = res.get('value')
        lines = value.get(line_type) if line_type in value else []

        for vals in lines:
            if vals.get('move_line_id'):
                vals['document_source'] = line_obj.get_document_source(
                    vals['move_line_id'])

    @api.multi
    def recompute_voucher_lines(
        self, partner_id, journal_id, price,
        currency_id, ttype, date
    ):

        res = super(account_voucher, self).recompute_voucher_lines(
            partner_id, journal_id, price,
            currency_id, ttype, date
        )

        self._get_source(res, 'line_cr_ids')
        self._get_source(res, 'line_dr_ids')

        return res
