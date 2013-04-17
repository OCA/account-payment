# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Domsense s.r.l. (<http://www.domsense.com>).
#    Copyright (C) 2012 Agile Business Group sagl (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp

class account_voucher(osv.osv):
    _inherit = "account.voucher"
    
    _columns = {
        'line_total': fields.float('Lines Total', digits_compute=dp.get_precision('Account'), readonly=True),
        }
    
    def balance_move(self, cr, uid, move_id, context=None):
        currency_obj = self.pool.get('res.currency')
        move = self.pool.get('account.move').browse(cr, uid, move_id, context)
        amount = 0.0
        for line in move.line_id:
            amount += line.debit - line.credit
        amount = currency_obj.round(cr, uid, move.company_id.currency_id, amount)
        # check if balance differs for more than 1 decimal according to account decimal precision
        if  abs(amount * 10 ** dp.get_precision('Account')(cr)[1]) > 1:
            raise osv.except_osv(_('Error'), _('The generated payment entry is unbalanced for more than 1 decimal'))
        if not currency_obj.is_zero(cr, uid, move.company_id.currency_id, amount):
            for line in move.line_id:
                # adjust the first move line that's not receivable, payable or liquidity
                if line.account_id.type != 'receivable' and line.account_id.type != 'payable' and line.account_id.type != 'liquidity':
                    if line.credit:
                        line.write({
                            'credit': line.credit + amount,
                            }, update_check=False)
                    elif line.debit:
                        line.write({
                            'debit': line.debit - amount,
                            }, update_check=False)
                    if line.tax_amount:
                        line.write({
                            'tax_amount': line.tax_amount + amount,
                            }, update_check=False)
                    break
        return amount
        
    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        res = super(account_voucher,self).voucher_move_line_create(cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context)
        self.write(cr, uid, voucher_id, {'line_total': res[0]}, context)
        return res
        
    def get_invoice_total(self, invoice):
        res = 0.0
        for inv_move_line in invoice.move_id.line_id:
            if inv_move_line.account_id.type in ('receivable','payable'):
                res += inv_move_line.debit or inv_move_line.credit # can both be presents?
        return res
        
    def allocated_amounts_grouped_by_invoice(self, cr, uid, voucher, context=None):
        '''
        
        this method builds a dictionary in the following form
        
        {
            first_invoice_id: {
                'allocated': 120.0,
                'total': 120.0,
                'write-off': 20.0,
                }
            second_invoice_id: {
                'allocated': 50.0,
                'total': 100.0,
                'write-off': 0.0,
                }
        }
        
        every amout is expressed in company currency.
        
        In order to compute cashed amount correctly, write-off will be subtract to reconciled amount.
        If more than one invoice is paid with this voucher, we distribute write-off equally (if allowed)
        
        '''
        res={}
        company_currency = super(account_voucher,self)._get_company_currency(cr, uid, voucher.id, context)
        current_currency = super(account_voucher,self)._get_current_currency(cr, uid, voucher.id, context)
        for line in voucher.line_ids:
            if line.amount and line.move_line_id and line.move_line_id.invoice:
                if not res.has_key(line.move_line_id.invoice.id):
                    res[line.move_line_id.invoice.id] = {
                        'allocated': 0.0,
                        'total': 0.0,
                        'write-off': 0.0,}
                current_amount = line.amount
                if company_currency != current_currency:
                    current_amount = super(account_voucher,self)._convert_amount(cr, uid, line.amount, voucher.id, context)
                res[line.move_line_id.invoice.id]['allocated'] += current_amount
                res[line.move_line_id.invoice.id]['total'] = self.get_invoice_total(line.move_line_id.invoice)
        if res:
            write_off_per_invoice = voucher.line_total / len(res.keys())
            if not voucher.company_id.allow_distributing_write_off and  len(res.keys()) > 1 and write_off_per_invoice:
                raise osv.except_osv(_('Error'), _('You are trying to pay with write-off more than one invoice and distributing write-off is not allowed. See company settings.'))
            if voucher.type == 'payment' or voucher.type == 'purchase':
                write_off_per_invoice = - write_off_per_invoice
            for inv_id in res:
                res[inv_id]['write-off'] = write_off_per_invoice
        return res
