# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


class account_move_line_payment(osv.osv_memory):
    _name = "account.move.line.payment"
    _description = "Pay Account Move Lines"

    def pay_move_lines(self, cr, uid, ids, context=None):
        obj_move_line = self.pool.get('account.move.line')
        if context is None:
            context = {}
        res = obj_move_line.pay_move_lines(cr, uid, context['active_ids'], context)
        res ['nodestroy'] =False
        return res
        
account_move_line_payment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

