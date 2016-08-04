# -*- coding: utf-8 -*-
# © initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    @api.model
    def _get_providers(self):
        providers = super(PaymentAcquirer, self)._get_providers()
        providers.append(['bitcoin', 'Bitcoin Transfer'])
        return providers

    @api.multi
    def bitcoin_get_form_action_url(self):
        return '/payment/bitcoin/feedback'
