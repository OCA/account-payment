# -*- coding: utf-8 -*-
# © 2013 Agile Business Group sagl
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class AccountVoucher(models.Model):

    _inherit = 'account.voucher'

    @api.multi
    def recompute_voucher_lines(
        self, partner_id, journal_id, price, currency_id, ttype, date
    ):
        res = super(AccountVoucher, self).recompute_voucher_lines(
            partner_id, journal_id, price, currency_id, ttype, date)

        line_obj = self.env['account.voucher.line']

        def update_move_line(vals):
            vals['supplier_invoice_number'] = line_obj.get_suppl_inv_num(
                vals['move_line_id'])

        if res.get('value') and res['value'].get('line_cr_ids'):
            for vals in res['value']['line_cr_ids']:
                if vals.get('move_line_id'):
                    update_move_line(vals)

        if res.get('value') and res['value'].get('line_dr_ids'):
            for vals in res['value']['line_dr_ids']:
                if vals.get('move_line_id'):
                    update_move_line(vals)
        return res
