# -*- coding: utf-8 -*-
# © 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#        Jordi Esteve <jesteve@zikzakmedia.com>
# © 2011 Domsense srl (<http://www.domsense.com>)
# © 2011-2017 Agile Business Group (<http://www.agilebg.com>)
# © 2015 Andrea Cometa <info@andreacometa.it>
# © 2015 Eneko Lacunza <elacunza@binovo.es>
# © 2015 Tecnativa (http://www.tecnativa.com)
# © 2016 Eficent Business and IT Consulting Services S.L.
#        (http://www.eficent.com)
# © 2016 David Dufresne <david.dufresne@savoirfairelinux.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': "Payments Due list",
    'version': '10.0.2.0.0',
    'category': 'Generic Modules/Payment',
    'author': 'Odoo Community Association (OCA), '
              'Agile Business Group, '
              'Tecnativa,'
              'Zikzakmedia SL',
    'website': 'http://www.agilebg.com',
    'license': 'AGPL-3',
    "depends": [
        'account_accountant',
    ],
    "data": [
        'views/payment_view.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
    "installable": True
}
