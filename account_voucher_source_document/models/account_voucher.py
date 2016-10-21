# -*- coding: utf-8 -*-
# © 2013 Agile Business Group sagl
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class account_voucher(models.Model):

    _inherit = 'account.voucher'

    @api.model
    def _get_source(self, res, line_type):
        line_obj = self.env['account.voucher.line']
        value = res.get('value')
        lines = value.get(line_type) if line_type in value else []

        for vals in lines:
            if isinstance(vals, tuple):
                if vals[0] == 0:
                    vals = vals[2]
                else:
                    continue
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
