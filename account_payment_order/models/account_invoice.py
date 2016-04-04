# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _get_reference_type(self):
        rt = super(AccountInvoice, self)._get_reference_type()
        rt.append(('structured', _('Structured Reference')))
        return rt
