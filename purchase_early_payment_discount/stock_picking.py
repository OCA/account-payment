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
from openerp import models, api


class StockPicking(models.Model):
    """
        Inherit stock_picking to add early payment discount from purchase order
    """

    _inherit = "stock.picking"

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        if picking and picking.move_lines and \
                picking.move_lines[0].purchase_line_id and \
                picking.move_lines[0].purchase_line_id.order_id.early_payment_discount:
            vals['early_payment_discount'] = \
                picking.move_lines[0].purchase_line_id.order_id.early_payment_discount

        return super(StockPicking, self)._create_invoice_from_picking(picking,
                                                                       vals)
