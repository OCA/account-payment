# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2012 7 i TRIA <http://www.7itria.cat>
#    Copyright (c) 2011-2012 Avanzosc <http://www.avanzosc.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados <http://www.serviciosbaeza.com>
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2014 initOS GmbH & Co. KG <http://initos.com/>
#                       Markus Schneider <markus.schneider at initos.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from osv import orm, fields
import decimal_precision as dp
import time


class payment_return_line(orm.Model):
    _name = "payment.return.line"
    _description = 'Payment return lines'

    _columns = {
        'return_id': fields.many2one('payment.return', 'Payment return',
                                     required=True, ondelete='cascade'),
        'concept': fields.char('Concept',
                               help="Readed from imported file. "
                               "Only for reference."),
        'reason': fields.char('Return reason',
                              help="Readed from imported file. "
                              "Only for reference."),
        'invoice_id': fields.many2one('account.invoice', 'Associated invoice'),
        'date': fields.date('Return date',
                            help="Readed from imported file. "
                            "Only for reference."),
        'notes': fields.text('Notes'),
        'partner_name': fields.char('Partner name',
                                    help="Readed from imported file. "
                                    "Only for reference."),
        'partner_id': fields.many2one('res.partner', 'Customer',
                                      domain="[('customer', '=', True)]"),
        'amount': fields.float('Amount',
                               help="Amount customer returns, "
                               "can be different from invoice amount",
                               digits_compute=dp.get_precision('Account')),
        'reconcile_id': fields.many2one('account.move.reconcile', 'Reconcile',
                                        help="Reference to the "
                                        "reconcile object."),
    }

    _defaults = {
        'date': lambda *x: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
