# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010 Pexego S.L. (http://www.pexego.es) All Rights Reserved.
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

"""
Extension of the purchase orders to add payment info.

Based on the sale_payment module.
"""
__author__ = "Borja López Soilán (Pexego) <borjals@pexego.es>"

import netsvc
from osv import fields, osv

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
        'payment_term': fields.many2one('account.payment.term', 'Payment Term', help='The payment terms. They will be transferred to the invoice.'),
        'payment_type': fields.many2one('payment.type', 'Payment type', help='The type of payment. It will be transferred to the invoice.'),
        'partner_bank': fields.many2one('res.partner.bank','Bank Account', select=True, help='The bank account to pay to or to be paid from. It will be transferred to the invoice.'),
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        """
        Extends the onchange to set the payment info of the partner.
        """
        result = super(purchase_order, self).onchange_partner_id(cr, uid, ids, partner_id)
        paytype_id = False
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            paytype_id = partner.payment_type_supplier.id
            result['value']['payment_type'] = paytype_id
            partner_payment_term_id = partner.property_payment_term_supplier and partner.property_payment_term_supplier.id or False
            result['value']['payment_term'] = partner_payment_term_id

        return self.onchange_paytype_id(cr, uid, ids, paytype_id, partner_id, result)

    def onchange_paytype_id(self, cr, uid, ids, paytype_id, partner_id, result = {'value': {}}):
        """
        Detect changes of the payment type and set the bank account accordingly.
        """
        if paytype_id and partner_id:
            paytype = self.pool.get('payment.type').browse(cr, uid, paytype_id)
            if paytype.suitable_bank_types and paytype.active:
                # if the payment type is related to a bank account
                partner_bank_obj = self.pool.get('res.partner.bank')
                args = [('partner_id', '=', partner_id), ('default_bank', '=', 1)]
                bank_account_id = partner_bank_obj.search(cr, uid, args)
                if bank_account_id:
                    result['value']['partner_bank'] = bank_account_id[0]
                    return result
        result['value']['partner_bank'] = False
        return result

    def action_invoice_create(self, cr, uid, ids, *args):
        """
        Extend the invoice creation action to preset the payment options.
        """
        # Create the invoice as usual.
        invoice_id = super(purchase_order, self).action_invoice_create(cr, uid, ids, args)

        #
        # Check if the order has payment info.
        #
        vals = {}
        for order in self.browse(cr, uid, ids):
            if order.payment_type:
                vals['payment_term'] = order.payment_term.id
            if order.payment_type:
                vals['payment_type'] = order.payment_type.id
            if order.partner_bank:
                vals['partner_bank'] = order.partner_bank.id
        if vals:
            # Write the payment info into the invoice.
            self.pool.get('account.invoice').write(cr, uid, [invoice_id], vals)
        return invoice_id

purchase_order()


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                                group=False, type='out_invoice', context=None):
        """
        Extend the invoice creation action to set the price type if needed.
        """
        # Create the invoices as usual-
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids,
                    journal_id=journal_id, group=group, type=type, context=context)

        for picking_id, invoice_id in res.items():
            picking = self.browse(cr, uid, picking_id, context=context)

            # Check if the picking comes from a purchase
            if picking.purchase_id:
                # Use the payment options from the order
                order = picking.purchase_id
                vals = {}
                if order.payment_term:
                    vals['payment_term'] = order.payment_term.id
                if order.payment_type:
                    vals['payment_type'] = order.payment_type.id
                if order.partner_bank:
                    vals['partner_bank'] = order.partner_bank.id
                if vals:
                    # Write the payment info into the invoice.
                    self.pool.get('account.invoice').write(cr, uid, [invoice_id], vals, context=context)
                    
        return res

stock_picking()


class res_partner(osv.osv):
    """
    Extends the partners to add a payment terms for purchases option.
    """
    _inherit = 'res.partner'

    _columns = {
        'property_payment_term_supplier': fields.property(
            'account.payment.term',
            type='many2one',
            relation='account.payment.term',
            string ='Payment Term',
            method=True,
            view_load=True,
            help="This payment term will be used instead of the default one for the current partner on purchases"),
    }
    
res_partner()


class account_invoice(osv.osv):
    """
    Extend the invoices to autoselect the payment terms,
    using either the supplier payment terms or the customer payment terms.
    """
    _inherit = 'account.invoice'

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        """
        Extend the onchange to use the supplier payment terms if this is
        a purchase invoice.
        """

        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id,
                            date_invoice=False, payment_term=False, partner_bank=False, company_id=False)

        #
        # Set the correct payment term
        #
        partner_payment_term_id = None
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if type in ('in_invoice', 'in_refund'):
                # Purchase invoice
                partner_payment_term_id = partner.property_payment_term_supplier and partner.property_payment_term_supplier.id or False
            else:
                # Sale invoice
                partner_payment_term_id = partner.property_payment_term and partner.property_payment_term.id or False

        result['value']['payment_term'] = partner_payment_term_id

        #
        # Recalculate the due date if needed
        #
        if payment_term != partner_payment_term_id:
            if partner_payment_term_id:
                to_update = self.onchange_payment_term_date_invoice(cr, uid, ids, partner_payment_term_id, date_invoice)
                result['value'].update(to_update['value'])
            else:
                result['value']['date_due'] = False

        return result

account_invoice()