# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
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


{
    "name": "VAT on payment",
    "version": "2.0",
    'category': 'Generic Modules/Accounting',
    "depends": ["account_voucher_cash_basis"],
    "author": "Agile Business Group",
    "description": """
    See 'account_voucher_cash_basis' description.
    
    To activate the VAT on payment behaviour, this module adds a checkbox on invoice form: 'Vat on payment'
    
    Moreover, three things have to be configured:
     - On account object, Related account used for real registrations on a VAT on payment basis
     - On journal object, Related journal used for shadow registrations on a VAT on payment basis
     - On tax code object, Related tax code used for real registrations on a VAT on payment basis
     
    Requirements: https://docs.google.com/spreadsheet/ccc?key=0Aodwq17jxF4edDJaZ2dOQkVEN0hodEtfRmpVdlg2Vnc#gid=0
    Howto:
    http://planet.domsense.com/en/2012/10/vat-on-payment-treatment-with-openerp/
    """,
    'website': 'http://www.agilebg.com',
    'init_xml': [],
    'update_xml': [
        'account_view.xml',
        'company_view.xml',
        ],
    'demo_xml': [], # TODO YAML tests
    'installable': True,
    'active': False,
}
