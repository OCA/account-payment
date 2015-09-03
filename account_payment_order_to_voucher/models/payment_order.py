# -*- coding: utf-8 -*-
#
#   See __openerp__.py about license
#

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class PaymentOrder(models.Model):
    _inherit = 'payment.order'
    voucher_ids = fields.Many2many(
        'account.voucher', string='Vouchers', readonly=True)

    def get_lines_by_partner(self, order):
        lines_by_partner = {}
        if order.voucher_ids:
            raise Warning(
                _("Payment order %s already has vouchers")
                % order.reference)
        if order.state != 'done':
            raise Warning(
                _("Payment order %s is not in 'done' state")
                % order.reference)
        for line in order.line_ids:
            if line.partner_id.id not in lines_by_partner:
                lines_by_partner[line.partner_id.id] = self.env['payment.line']
            lines_by_partner[line.partner_id.id] |= line
        return lines_by_partner

    def _compute_lines_total(self, payment_lines):
        return sum(payment_lines.mapped('amount_currency'))

    def _get_currency_id(self, payment_lines):
        currency_ids = payment_lines.mapped('currency').ids
        if len(currency_ids) > 1:
            raise Warning(
                _("Every order lines must have the same currency"))
        return currency_ids[0]

    def _build_voucher_header(self, payment_lines):
        total = self._compute_lines_total(payment_lines)

        # every line has the same order and partner
        order = payment_lines[0].order_id
        partner = payment_lines[0].partner_id

        currency_id = self._get_currency_id(payment_lines)
        voucher_vals = {
            'type': 'payment',
            'name': order.reference,
            'partner_id': partner.id,
            'journal_id': order.mode.journal.id,
            'account_id': order.mode.journal.default_debit_account_id.id,
            'company_id': order.company_id.id,
            'currency_id': currency_id,
            'date': order.date_done,
            'amount': total,
            }
        return voucher_vals

    def _build_voucher_lines(self, payment_lines, voucher):
        vals_list = []
        for line in payment_lines:
            vals = {
                'voucher_id': voucher.id,
                'type': 'dr',
                'account_id': line.move_line_id.account_id.id,
                'amount': line.amount_currency,
                'move_line_id': line.move_line_id.id,
                }
            vals_list.append(vals)
        return vals_list

    @api.multi
    def generate_vouchers(self):
        voucher_model = self.env['account.voucher']
        voucher_line_model = self.env['account.voucher.line']
        vouchers = []
        for order in self:
            order_vouchers = []
            lines_by_partner = self.get_lines_by_partner(order)
            for partner_id in lines_by_partner:
                payment_lines = lines_by_partner[partner_id]
                voucher_vals = self._build_voucher_header(payment_lines)
                voucher = voucher_model.create(voucher_vals)
                line_vals_list = self._build_voucher_lines(
                    payment_lines, voucher)
                for line_vals in line_vals_list:
                    voucher_line_model.create(line_vals)
                order_vouchers.append(voucher)
            order.voucher_ids = [v.id for v in order_vouchers]
            vouchers.extend(order_vouchers)

        action_res = self.env['ir.actions.act_window'].for_xml_id(
            'account_voucher', 'action_vendor_payment')
        action_res['domain'] = [('id', 'in', [v.id for v in vouchers])]
        return action_res
