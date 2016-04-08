# -*- coding: utf-8 -*-
# © 2013 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# © 2014 Markus Schneider <markus.schneider@initos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    returned_payment = fields.Boolean(
        string='Payment returned',
        help='Invoice has been included on a payment that has been returned '
             'later.')
