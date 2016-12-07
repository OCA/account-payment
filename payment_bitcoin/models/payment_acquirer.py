# -*- coding: utf-8 -*-
# © ZedeS Technologies, initOS GmbH 2016
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

    @api.cr_uid_ids_context
    def render(self, cr, uid, id, reference, amount, currency_id, tx_id=None, partner_id=False, partner_values=None, tx_values=None, context=None):
        if context and context.get('order_ref'):
            reference = context['order_ref']
        return super(PaymentAcquirer, self).render(cr, uid, id, reference, amount, currency_id, tx_id=tx_id, partner_id=partner_id, partner_values=partner_values, tx_values=tx_values, context=context)