# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import hashlib
from openerp import api, fields, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    sisow_issuer_id = fields.Char('Issuer')
    sisow_entrance_code = fields.Char('Entrance code')

    @api.model
    def _sisow_form_get_tx_from_data(self, data):
        transaction = self.env['payment.transaction'].sudo().search([
            ('acquirer_id.provider', '=', 'sisow'),
            ('acquirer_id.website_published', '=', True),
            ('acquirer_reference', '=', data['trxid']),
            ('sisow_entrance_code', '=', data['ec']),
        ])
        if not transaction or len(transaction) > 1:
            return False
        if not hashlib.sha1(
            data['trxid'] + data['ec'] + data['status'] +
            transaction.acquirer_id.sisow_merchant_id +
            transaction.acquirer_id.sisow_merchant_key
        ).hexdigest() == data['sha1']:
            return False
        return transaction

    @api.model
    def _sisow_form_validate(self, transaction, data):
        if not transaction:
            return False
        state = transaction.state
        if data['status'] == 'Success':
            state = 'done'
        elif data['status'] in ['Expired', 'Cancelled']:
            state = 'cancel'
        elif data['status'] == 'Failure':
            state = 'error'
        return transaction.write({
            'state': state,
        })
