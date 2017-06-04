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
from openerp import models, fields, api


class AccountPartnerPaymentTermEarlyDiscount(models.Model):
    """Objeto que une las empresas con plazos de pago y descuentos pronto
        pago"""

    _name = "account.partner.payment.term.early.discount"
    _description = "Early payment discounts"

    @api.model
    def _get_default_partner(self):
        """return id of active object if it is res.partner"""
        return self.env.context.get('partner_id', False)

    @api.model
    def _get_default_payment_term(self):
        """return id of active object if it is account.payment.term"""
        return self.env.context.get('payment_term', False)

    name = fields.Char('Name', size=64, required=True)
    partner_id = fields.Many2one('res.partner', 'Partner',
                                 default=_get_default_partner)
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term',
                                      default=_get_default_payment_term)
    early_payment_discount = fields.Float(
        'E.P. disc.(%)', digits=(16, 2), required=True,
        help="Percentage of discount for early payment.")
    sale_discount = fields.Boolean('Sale discount')
