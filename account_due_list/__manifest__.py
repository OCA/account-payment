# -*- coding: utf-8 -*-
##############################################################################
#
#  Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#  Copyright (C) 2011-2013 Agile Business Group sagl
#  (<http://www.agilebg.com>)
#  @author Jordi Esteve <jesteve@zikzakmedia.com>
#  @author Lorenzo Battistini <lorenzo.battistini@agilebg.com>
#  Ported to OpenERP 7.0 by Alex Comba <alex.comba@agilebg.com> and
#  Bruno Bottacini <bruno.bottacini@dorella.com>
#  Ported to Odoo by Andrea Cometa <a.cometa@apuliasoftware.it>
#
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
#
##############################################################################
{
    'name': "Payments Due list",
    'version': '10.0.1.0.0',
    'category': 'Generic Modules/Payment',
    'author': 'Odoo Italia Network, '
              'Odoo Community Association (OCA), '
              'Agile Business Group, '
              'Serv. Tecnol. Avanzados - Pedro M. Baeza,'
              'Zikzakmedia SL',
    'website': 'http://www.odoo-community.org',
    'license': 'AGPL-3',
    "depends": [
        'account',
    ],
    "data": [
        'views/payment_view.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    "installable": True,
}
