# -*- coding: utf-8 -*-
# © 2011-2012 Domsense s.r.l. (<http://www.domsense.com>).
# © 2014 Agile Business Group sagl (<http://www.agilebg.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields


class ResCompany(orm.Model):
    _inherit = "res.company"
    _columns = {
        'vat_on_payment': fields.boolean(
            'VAT on payment treatment',
            help="Company Selected applies VAT on payment."),
        'vat_payment_lines': fields.selection(
            [('shadow_move', 'Move to Shadow Move'),
             ('real_move', 'Keep on Real Move')],
            'VAT lines on Payment',
            default='shadow_move',
            help="Selection field to configure if the account moves "
                 "generated on VAT on payment basis should modify the "
                 "implicit account moves generated normally, and to move "
                 "the partner account move line to the shadow move."),
        'vat_config_error': fields.selection(
            [('raise_error', 'Raise Error'),
             ('use_the_same', 'Use the same')],
            'Missconfiguration on VAT on Payment',
            default='raise_error',
            help="Selection field to configure behaviour on missconfigured "
                 "datas on VAT on payment basis.\n"
                 " - 'Raise Error' is selected, if an account, journal "
                 "doesn't have set the corresponding VAT on payment "
                 "field, it will raise an error about missconfiguration.\n"
                 " - 'Use the same' is selected, it will not raise an error "
                 "about missconfiguration, and use the same account, journal "
                 "in VAT on payment.")
    }
