# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import hashlib
import json
import requests
import urllib
import mock
from openerp import http
from openerp.tests.common import HttpCase, HOST, PORT


class TestPaymentSisow(HttpCase):
    def _session_update(self, **kwargs):
        self.session.update(**kwargs)
        http.root.session_store.save(self.session)

    def url_open_json(self, url, data=None, timeout=10):
        return requests.post(
            'http://%s:%s%s' % (HOST, PORT, url),
            data=json.dumps(data or {}),
            headers={
                'content-type': 'application/json',
                'cookie': 'session_id=%s' % self.session_id,
            },
            timeout=timeout,
        )

    def test_payment_sisow(self):
        result = self.url_open('/payment/sisow/redirect')
        # should fail because there's no transaction
        self.assertEqual(result.code, 404)
        self._session_update(
            sale_transaction_id=self.env.ref(
                'payment_sisow.sisow_transaction'
            ).id
        )
        http.root.session_store.save(self.session)
        result = self.url_open('/payment/sisow/redirect')
        # should fail because there's no issuer
        self.assertEqual(result.code, 404)
        self.url_open_json('/payment/sisow/issuer/99')
        with mock.patch('requests.get', new=self._mock_request_get):
            result = self.url_open('/payment/sisow/redirect', timeout=3000)
            self.assertEqual(result.code, 200)
        result = self.url_open(
            '/payment/sisow/return',
            urllib.urlencode([
                ('status', 'Success'),
                ('trxid', '123456'),
                ('ec', 'wrong code'),
                ('csrf_token', http.WebRequest.csrf_token.__func__(self)),
            ]),
        )
        # should fail because we pass a wrong entrance code
        self.assertEqual(result.code, 404)

    def _mock_request_get(self, url, params):
        result = mock.Mock()

        acquirer = self.env.ref('payment_sisow.payment_acquirer')
        if url == ('https://www.sisow.nl/Sisow/iDeal/RestHandler.ashx/'
                   'TransactionRequest'):
            result.content = '''<?xml version="1.0" encoding="UTF-8"?>
            <transactionresponse
                xmlns="https://www.sisow.nl/Sisow/REST" version="1.0.0">
                <transaction>
                    <issuerurl>/shop/payment/validate</issuerurl>
                    <trxid>123456</trxid>
                </transaction>
                <signature>
                    <sha1>%s</sha1>
                </signature>
            </transactionresponse>
            ''' % hashlib.sha1(
                '123456/shop/payment/validate' +
                acquirer.sisow_merchant_id +
                acquirer.sisow_merchant_key
            ).hexdigest()
        return result
