# encoding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Zikzakmedia S.L. (http://zikzakmedia.com)
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
from openerp import models, fields, api
from openerp.addons.decimal_precision import decimal_precision as dp


class AccountInvoice(models.Model):
    """
        Inherit account.invoice to compute from button the early payment
        discount
    """

    _inherit = 'account.invoice'

    @api.one
    def compute_early_payment_lines(self):
        """creates early payment lines"""
        if self.type == 'in_invoice':
            return super(AccountInvoice, self.with_context(
                account_name='property_account_purchase_early_payment_disc',
                stock_account_name='property_stock_account_input')
                ).compute_early_payment_lines()
        return super(AccountInvoice, self).compute_early_payment_lines()

    @api.one
    @api.onchange('payment_term')
    def onchange_payment_term(self):
        """onchange event to update early payment discount when the payment
            term changes"""
        res = super(AccountInvoice, self).onchange_payment_term()
        if self.type == 'in_invoice':
            self.early_payment_discount = self._get_early_disc(
                [('purchase_discount', '=', True)])
