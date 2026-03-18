# SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from odoo import http
from odoo.http import request
from odoo.addons.payment_taler.utils.utils import talog, tawarn, taerror

class TalerController(http.Controller):
    _fulfillment_url = '/payment/taler/return'

    # Route that online payments use
    @http.route(_fulfillment_url + "/<string:taler_uuid>/<string:recvd_order_id>", type='http', auth='public', methods=['GET'])
    def taler_return_from_checkout(self, **data):
        talog("Returning after transaction completion. Taler_uuid: " + data['taler_uuid'] + ", Received_order_id: " + data['recvd_order_id'])
        reference = data.get('recvd_order_id')
        transaction = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        if not transaction:
            taerror("No transaction found for reference: ", data.get('recvd_order_id'))
            return
        # Fetches the current taler merchant order status from the transaction
        received_taler_order_id, taler_order_status = transaction._get_orderid_status()
        if received_taler_order_id != transaction.taler_order_id:
            taerror("OrderID do not match for reference: ", reference)
            return
        if data.get('taler_uuid') != transaction.taler_uuid:
            taerror("UUID do not match for reference: ", reference)
            return
        data = {'reference': data.get('recvd_order_id'),
                'merchantOrderId': transaction.taler_order_id,
                'paymentStatus': taler_order_status
        }
        transaction._handle_notification_data('taler', data)

        return request.redirect('/payment/status')

    # Route that invoices use
    @http.route(_fulfillment_url + "/<string:taler_uuid>/<string:prefix>/<int:year>/<string:number>/", type='http', auth='public')
    def taler_return_from_invoice(self, **data):
        reference = data.get('prefix') + "/" + str(data.get('year')) + "/" + data.get('number')
        talog("Returning after invoice payment completion. taler_uuid: " + data['taler_uuid'] + ", reference: " + reference)
        # Searches in all transactions, one that has the reference received
        transaction = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        if not transaction:
            taerror("No transaction found for reference: ", data.get('recvd_order_id'))
            return
        # Fetches the current taler merchant order status from the transaction
        received_taler_order_id, taler_orderStatus = transaction._get_orderid_status()
        if received_taler_order_id != transaction.taler_order_id:
            taerror("OrderID do not match for reference: ", reference)
            return
        if data.get('taler_uuid') != transaction.taler_uuid:
            taerror("UUID do not match for reference: ", reference)
            return
        data = {'reference': reference,
                'merchantOrderId': transaction.taler_order_id,
                'paymentStatus': taler_orderStatus
        }
        transaction._handle_notification_data('taler', data)

        return request.redirect('/payment/status')
