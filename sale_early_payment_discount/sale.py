# encoding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class SaleOrder(models.Model):
    """Inherit sale_order to add early payment discount"""

    _inherit = 'sale.order'

    early_payment_discount = fields.Float('E.P. disc.(%)', digits=(16, 2),
                                          help="Early payment discount")
    early_payment_disc_total = fields.Float(
        'With E.P.', digits_compute=dp.get_precision('Account'),
        compute='_amount_all2')
    early_payment_disc_untaxed = fields.Float(
        'Untaxed Amount E.P.',  digits_compute=dp.get_precision('Account'),
        compute='_amount_all2')
    early_payment_disc_tax = fields.Float(
        'Taxes E.P.', digits_compute=dp.get_precision('Account'),
        compute='_amount_all2')
    total_early_discount = fields.Float(
        'E.P. amount', digits_compute=dp.get_precision('Account'),
        compute='_amount_all2')

    @api.one
    @api.depends('order_line', 'early_payment_discount',
                 'order_line.price_unit', 'order_line.tax_id',
                 'order_line.discount', 'order_line.product_uom_qty')
    def _amount_all2(self):
        """calculates functions amount fields"""
        if not self.early_payment_discount:
            self.early_payment_disc_total = self.amount_total
            self.early_payment_disc_tax = self.amount_tax
            self.early_payment_disc_untaxed = self.amount_untaxed
        else:
            self.early_payment_disc_tax = self.amount_tax * \
                (1.0 - (float(self.early_payment_discount or 0.0)) / 100.0)
            self.early_payment_disc_untaxed = self.amount_untaxed * \
                (1.0 - (float(self.early_payment_discount or 0.0)) / 100.0)
            self.early_payment_disc_total = self.early_payment_disc_untaxed + \
                self.early_payment_disc_tax
            self.total_early_discount = self.early_payment_disc_untaxed - \
                self.amount_untaxed

    @api.multi
    def _calc_early_discount_percentage(self):
        self.ensure_one()
        early_payment_term_obj = \
            self.env['account.partner.payment.term.early.discount']
        if self.payment_term:
            early_discs = early_payment_term_obj.search(
                [('partner_id', '=', self.partner_id.id), ('payment_term_id',
                                                           '=',
                                                           self.payment_term.id
                                                           ),
                 ('sale_discount', '=', True)])
            if not early_discs:
                early_discs = early_payment_term_obj.search(
                    [('partner_id', '=', self.partner_id.id),
                     ('payment_term_id', '=', False),
                     ('sale_discount', '=', True)])
                if not early_discs:
                    early_discs = early_payment_term_obj.search(
                        [('partner_id', '=', False), ('payment_term_id', '=',
                                                      self.payment_term.id),
                         ('sale_discount', '=', True)])
        else:
            early_discs = early_payment_term_obj.search(
                [('partner_id', '=', self.partner_id.id), ('payment_term_id',
                                                           '=', False),
                 ('sale_discount', '=', True)])
        if early_discs:
            return early_discs[0].early_payment_discount
        else:
            return 0.0

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id2(self):
        """
            extend this event for delete early payment discount if it isn't
            valid to new partner or add new early payment discount
        """
        res = self.onchange_partner_id(self.partner_id.id)
        if not self.partner_id:
            return res
        if res.get('value', False):
            for field in res['value'].keys():
                self[field] = res['value'][field]
            res.pop('value', False)
        self.early_payment_discount = self._calc_early_discount_percentage()
        return res

    @api.one
    @api.onchange('payment_term')
    def onchange_payment_term(self):
        """
            onchange event to update early payment dicount when the payment
            term changes
        """
        self.early_payment_discount = self._calc_early_discount_percentage()

    @api.multi
    def action_invoice_create(self, grouped=False,
                              states=['confirmed', 'done', 'exception'],
                              date_invoice=False):
        """
            Inherited method for writing early_payment_discount value in
            created invoice
        """
        invoice_id = super(SaleOrder, self).action_invoice_create(
            grouped=grouped, states=states, date_invoice=date_invoice)
        invoice = self.env['account.invoice'].browse(invoice_id)
        current_sale = self and self[0] or False
        if current_sale.early_payment_discount:
            invoice.write({'early_payment_discount':
                           current_sale.early_payment_discount})
        return invoice_id
