# SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from odoo.tests import tagged, TransactionCase
from odoo.addons.payment.tests.common import PaymentCommon


@tagged('taler')
class TestTalerCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.currency_eur = cls._prepare_currency('EUR') # Supported currency
        cls.currency_chf = cls._prepare_currency('CHF') # Supported currency
        cls.currency_zar = cls._prepare_currency('ZAR') # Unsupported currency
        cls.taler_provider = cls._prepare_provider('taler', update_values={
            'taler_merchant_url': 'https://backend.demo.taler.net/instances/sandbox',
            'taler_merchant_password': 'dummy password',
            'taler_token': 'dummy token',
            'fulfillment_message': 'dummy fulfillment message'
        }) # Provider dummy data

        cls.provider = cls.taler_provider
        cls.currency = cls.currency_chf # Assign one of the currencies as default

        cls.notification_data = {'reference': '01234567899876543210',
                                 'merchantOrderId': '98765432100123456789',
                                 'paymentStatus': 'paid'
        }
