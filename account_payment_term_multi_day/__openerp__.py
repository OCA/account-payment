# encoding: utf-8
##############################################################################
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
    'name': "Multiple payment days for payment terms",
    'version': "8.0.1.0.0",
    'author': "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Odoo Community Association (OCA)",
    'category': 'Accounting',
    'contributors': [
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>'
    ],
    'license': "AGPL-3",
    'depends': [
        'account',
    ],
    'data': [
        'views/account_payment_term_view.xml',
    ],
    "post_init_hook": "copy_payment_day",
    'installable': True,
}
