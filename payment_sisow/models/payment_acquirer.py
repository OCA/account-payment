# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import hashlib
import requests
import urllib
import uuid
import logging
from lxml import etree
from openerp import api, fields, models
_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    _sisow_rest_url = 'https://www.sisow.nl/Sisow/iDeal/RestHandler.ashx/'

    @api.model
    def _get_providers(self):
        result = super(PaymentAcquirer, self)._get_providers()
        result.append(('sisow', 'Sisow'))
        return result

    sisow_merchant_id = fields.Char(
        'Merchant ID', required_if_provider='sisow',
        help='Your merchant ID as given by Sisow',
    )
    sisow_merchant_key = fields.Char(
        'Merchant key', required_if_provider='sisow',
        help='Your merchant key as given by Sisow',
    )
    sisow_shop_id = fields.Char(
        'Shop ID', required_if_provider='sisow', default='0',
        help='Your shop ID, 0 if in doubt',
    )

    @api.multi
    def _sisow_request(self, name, **params):
        """Return the result of a request as parsed xml"""
        result = requests.get(self._sisow_rest_url + name, params=params)
        return etree.fromstring(result.content)

    @api.model
    def _sisow_xpath(self, document, xpath):
        """Run an xpath with the sisow namespace"""
        return document.xpath(
            xpath,
            namespaces={'sisow': 'https://www.sisow.nl/Sisow/REST'},
        )

    @api.multi
    def _sisow_issuers(self):
        issuers = self._sisow_request(
            'DirectoryRequest', test=self.environment != 'prod'
        )
        return [
            {
                'id': self._sisow_xpath(issuer, './sisow:issuerid')[0].text,
                'name':
                self._sisow_xpath(issuer, './sisow:issuername')[0].text,
            }
            for issuer in self._sisow_xpath(issuers, '//sisow:issuer')
        ]

    @api.multi
    def _sisow_request_transaction(self, transaction, issuer_id, return_url):
        if transaction.acquirer_reference:
            _logger.info(
                'Restarting transaction %d, old values were '
                'Issuer: %s, '
                'Acquirer reference: %s, '
                'Entrance code: %s',
                transaction.id,
                transaction.sisow_issuer_id,
                transaction.acquirer_reference,
                transaction.sisow_entrance_code,
            )
        purchaseid = transaction.reference
        entrancecode = uuid.uuid4().hex
        amount = '%d' % (transaction.sudo().sale_order_id.amount_total * 100)
        result = self._sisow_request(
            'TransactionRequest',
            shopid=self.sisow_shop_id,
            merchantid=self.sisow_merchant_id,
            payment='',
            purchaseid=purchaseid,
            description=purchaseid[:32],
            amount=amount,
            issuerid=issuer_id,
            testmode='true' if self.environment != 'prod' else '',
            entrancecode=entrancecode,
            returnurl=return_url,
            sha1=hashlib.sha1(
                purchaseid + entrancecode + amount + self.sisow_shop_id +
                self.sisow_merchant_id + self.sisow_merchant_key
            ).hexdigest(),
        )
        error = self._sisow_xpath(result, '//sisow:error')
        if error:
            raise Exception(
                self._sisow_xpath(error[0], '//sisow:errorcode')[0].text,
                self._sisow_xpath(error[0], '//sisow:errormessage')[0].text,
            )

        issuerurl = self._sisow_xpath(result, '//sisow:issuerurl')[0].text
        transaction_id = self._sisow_xpath(result, '//sisow:trxid')[0].text
        sha1 = self._sisow_xpath(result, '//sisow:sha1')[0].text
        assert hashlib.sha1(
            transaction_id + issuerurl + self.sisow_merchant_id +
            self.sisow_merchant_key
        ).hexdigest() == sha1, 'Invalid message received'
        issuerurl = urllib.unquote(issuerurl)
        transaction.sudo().write({
            'acquirer_reference': transaction_id,
            'sisow_issuer_id': issuer_id,
            'sisow_entrance_code': entrancecode,
            'state': 'pending',
        })
        return issuerurl
