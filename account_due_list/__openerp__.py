# -*- coding: utf-8 -*-
# © 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#        Jordi Esteve <jesteve@zikzakmedia.com>
# © 2011 Domsense srl (<http://www.domsense.com>)
# © 2011-2013 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2015 Andrea Cometa <info@andreacometa.it>
# © 2015 Eneko Lacunza <elacunza@binovo.es>
# © 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Receivables and Payables Open Items",
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/Payment',
    'author': 'Odoo Community Association (OCA), '
              'Agile Business Group, '
              'Tecnativa,'
              'Zikzakmedia SL,'
              'Eficent',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends": [
        'account',
    ],
    "data": [
        'views/receivables_payables_view.xml',
    ],
    "installable": True,
}
