# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2012 7 i TRIA <http://www.7itria.cat>
#    Copyright (c) 2011-2012 Avanzosc <http://www.avanzosc.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados <http://www.serviciosbaeza.com>
#                       Pedro M. Baeza <pedro.baeza at serviciosbaeza.com>
#    Copyright (c) 2014 initOS GmbH & Co. KG <http://initos.com/>
#                       Markus Schneider <markus.schneider at initos.com>
#    Copyright (c) 2015 Incaser Informatica <http://www.incaser.es/>
#                       Sergio Teruel <sergio at incaser.es>
#    Copyright (c) 2015 Serv. Tecnol. Avanzados <http://www.serviciosbaeza.com>
#                       Pedro M. Baeza <pedro.baeza at serviciosbaeza.com>
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


{
    "name": "Account Payment Returns",
    "version": "8.0.1.0.0",
    "summary": "Manage the return of your payments",
    'license': 'AGPL-3',
    "depends": [
        'mail',
        'account',
    ],
    'author': '7 i TRIA, '
              'Serv. Tecnol. Avanzados - Pedro M. Baeza, '
              'Incaser Informática, '
              'initOS GmbH & Co., '
              'Odoo Community Association (OCA)',
    'website': 'http://www.serviciosbaeza.com',
    'data': [
        'security/ir.model.access.csv',
        'security/account_payment_return_security.xml',
        'views/payment_return_view.xml',
        'data/ir_sequence_data.xml',
        'views/account_invoice_view.xml',
    ],
    'installable': True,
}
