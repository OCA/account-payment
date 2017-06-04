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


def intersect(la, lb):
    """returns True for equal keys in two lists"""
    l = filter(lambda x: x in lb, la)
    return len(l) == len(la) == len(lb)


class AccountInvoice(models.Model):
    """Inherit account_invoice to compute from button the early payment
       discount"""

    _inherit = 'account.invoice'

    early_payment_discount = fields.Float('E.P. disc.(%)', digits=(16, 2),
                                          help="Early payment discount")
    early_discount_amount = fields.Float(
        'E.P. amount', digits_compute=dp.get_precision('Account'),
        help="Early payment discount amount to apply.", readonly=True,
        compute='_get_early_discount_amount')

    @api.one
    def _get_early_discount_amount(self):
        """obtain early_payment_discount_amount"""
        res = {}
        prod_early_payment_id = self.env['product.product'].search(
            [('default_code', '=', 'DPP')])
        prod_early_payment_id = prod_early_payment_id and \
            prod_early_payment_id[0] or False

        if prod_early_payment_id:
            if not self.early_payment_discount:
                self.early_payment_discount_amount = 0.0

            #searches if DPP is applied
            found = False
            for line in self.invoice_line:
                if line.product_id and line.product_id.id == \
                        prod_early_payment_id.id:
                    found = True
                    break

            if found:
                self.early_payment_discount_amount = 0.0
            else:
                total_net_price = 0.0
                for invoice_line in self.invoice_line:
                    total_net_price += invoice_line.price_subtotal

                self.early_payment_discount_amount = float(total_net_price) - \
                    (float(total_net_price) * (1 - (self.early_payment_discount
                                                    or 0.0) / 100.0))

    @api.multi
    def _get_early_disc(self, domain):
        """
            Seeks the  early payment discount appropriate for the invoice
        """
        self.ensure_one()
        early_disc_obj = \
            self.env['account.partner.payment.term.early.discount']
        early_discs = False
        early_discs = early_disc_obj.search(
            domain + [('partner_id', '=', self.partner_id.id),
                      ('payment_term_id', '=', self.payment_term.id)])
        if not early_discs:
            early_discs = early_disc_obj.search(
                domain + [('partner_id', '=', self.partner_id.id),
                          ('payment_term_id', '=', False)])
            if not early_discs and self.payment_term:
                early_discs = early_disc_obj.search(
                    domain + [('partner_id', '=', False),
                              ('payment_term_id', '=', self.payment_term.id)])
        return early_discs and early_discs.early_payment_discount or False

    @api.multi
    def compute_early_payment_discount(self, invoice_lines,
                                       early_payment_percentage):
        """computes early payment price_unit"""
        total_net_price = 0.0

        for invoice_line in invoice_lines:
            total_net_price += invoice_line.price_subtotal

        return float(total_net_price) - (float(total_net_price) *
                                         (1 - (float(early_payment_percentage)
                                               or 0.0) / 100.0))

    @api.one
    def compute_early_payment_lines(self):
        """creates early payment lines"""
        early_payments = {}
        inv_lines_out_vat = self.env['account.invoice.line']

        for invoice_line in self.invoice_line:
            if invoice_line.invoice_line_tax_id:
                line_tax_ids = [x.id for x in invoice_line.invoice_line_tax_id]
                found = False

                for key in early_payments:
                    if intersect([int(x) for x in key.split(",")],
                                 line_tax_ids):
                        early_payments[key] += invoice_line
                        found = True
                        break

                if not found:
                    tax_str = ",".join([str(x) for x in line_tax_ids])
                    early_payments[tax_str] = invoice_line
            else:
                #lines without vat defined
                inv_lines_out_vat += invoice_line

        prod_early_payment = self.env['product.product'].search(
            [('default_code', '=', 'DPP')])
        prod_early_payment = prod_early_payment and prod_early_payment[0] or \
            False

        if prod_early_payment:
            group_account = {}
            for early_payment_line in early_payments:
                group_account_line = {}

                for invoice_line in early_payments[early_payment_line]:
                    product_categ = invoice_line.product_id.categ_id
                    acc_name = 'property_account_sale_early_payment_disc'
                    stock_acc_name = 'property_stock_account_output'
                    if self.env.context.get('account_name', False):
                        acc_name = self.env.context['account_name']
                    if self.env.context.get('stock_account_name', False):
                        stock_acc_name = self.env.context['stock_account_name']
                    account_early_payment_disc = product_categ and \
                        product_categ[acc_name]
                    stock_account = prod_early_payment[stock_acc_name]

                    if account_early_payment_disc and \
                            account_early_payment_disc.id not in \
                            group_account_line:
                        group_account_line[account_early_payment_disc.id] = \
                            invoice_line
                    elif account_early_payment_disc and \
                            account_early_payment_disc.id in \
                            group_account_line:
                        group_account_line[account_early_payment_disc.id] += \
                            invoice_line
                    elif stock_account and stock_account.id not in \
                            group_account_line:
                        group_account_line[stock_account.id] = invoice_line
                    elif stock_account and stock_account.id in \
                            group_account_line or \
                            account_early_payment_disc.id and  \
                            account_early_payment_disc.id in \
                            group_account_line:
                        group_account_line[stock_account.id] += \
                            invoice_line
                    else:
                        raise exceptions.except_orm(_('Warning'),
                                                    _('Cannot set early \
payment discount because now is impossible find the early payment account. \
Review invoice products categories have defined early payment account by \
default or early payment discount product have defined an output account.'))
                group_account[early_payment_line] = group_account_line

            for early_payment_line in group_account:
                for account_id in group_account[early_payment_line]:
                    self.env['account.invoice.line'].create({
                        'name': _("Early payment discount") + " " +
                        str(self.early_payment_discount) + "%",
                        'invoice_id': self.id,
                        'product_id': prod_early_payment.id,
                        'account_id': account_id,
                        'price_unit': 0.0 -
                        self.compute_early_payment_discount(
                            group_account[early_payment_line][account_id],
                            self.early_payment_discount),
                        'quantity': 1,
                        'invoice_line_tax_id':
                        [(6, 0, [int(x) for x in
                                 early_payment_line.split(',')])]
                        })

            if inv_lines_out_vat:
                prod_categ = prod_early_payment.categ_id
                account_id = prod_categ and \
                    prod_categ.property_account_sale_early_payment_disc.id or \
                    prod_early_payment.property_stock_account_output.id

                self.env['account.invoice.line'].create({
                    'name': _("Early payment discount") + " " +
                    str(self.early_payment_discount) + "%",
                    'invoice_id': self.id,
                    'product_id': prod_early_payment.id,
                    'account_id': account_id,
                    'price_unit': 0.0 - self.compute_early_payment_discount(
                        inv_lines_out_vat, self.early_payment_discount),
                    'quantity': 1
                    })

        #recompute taxes
        self.button_compute(set_total=(type in ('in_invoice', 'in_refund')))
        return True

    @api.one
    def button_compute_early_payment_disc(self):
        """computes early payment discount in invoice"""
        self.ensure_one()
        # create list with all early discount lines to delete,
        # new early discount lines will be created
        orig_early_payment_lines = self.env['account.invoice.line'].search(
            [('product_id.default_code', '=', 'DPP'),
             ('invoice_id', '=', self.id)])
        orig_early_payment_lines.unlink()
        if self.early_payment_discount:
            self.compute_early_payment_lines()
        return True

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id2(self):
        res = super(AccountInvoice, self).onchange_partner_id(
            self.type, self.partner_id.id, self.date_invoice,
            self.payment_term.id, self.partner_bank_id.id, self.company_id.id)
        if not self.partner_id:
            return res
        if res.get('value', False):
            for field in res['value'].keys():
                self[field] = res['value'][field]
            res.pop('value', False)
        self.onchange_payment_term()
        return res

    @api.one
    @api.onchange('payment_term')
    def onchange_payment_term(self):
        """onchange event to update early payment discount when the payment
            term changes"""
        if not self.payment_term:
            self.early_payment_discount = False
            return
        if self.type == 'out_invoice':
            self.early_payment_discount = self._get_early_disc(
                [('sale_discount', '=', True)])
