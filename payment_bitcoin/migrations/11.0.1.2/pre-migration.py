# Copyright 2017 Tecnativa - Pedro M. Baeza
# Copyright 2018 - Nicolas JEUDY
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_xmlid_renames = [
    ('payment_bitcoin.bitcoin_rate_default', 'payment_bitcoin.bitcoin_rate_default'),
    ('payment_bitcoin.payment_icon_bitcoin', 'payment_bitcoin.payment_icon_bitcoin'),
    ('payment_bitcoin.payment_acquirer_bitcoin', 'payment_bitcoin.payment_acquirer_bitcoin'),
]


#@openupgrade.migrate()
#def migrate(env, version):
#    openupgrade.rename_xmlids(env.cr, _xmlid_renames)
