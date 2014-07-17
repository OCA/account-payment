# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2012 7 i TRIA <http://www.7itria.cat>
#    Copyright (c) 2011-2012 Avanzosc <http://www.avanzosc.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com> 
#    Copyright (c) 2014 initOS GmbH & Co. KG <http://initos.com/>
#                       Markus Schneider <markus.schneider at initos.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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


{
    "name" : "Account Payment Return",
    "version" : "1.0",
    'license': 'AGPL-3',
    "depends" : ['account'],
    'author': 'initOS GmbH & Co. KG',
    'website' : 'http://www.initos.com',
    "description": """
    Provides a object to handle payment returns
    """,
    'data': [
            'security/ir.model.access.csv',
            'security/account_payment_return_security.xml',
            'payment_return_view.xml',
            'payment_return_data.xml',
            'account_invoice_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
