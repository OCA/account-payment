from mock import patch

from odoo.addons.account_payment_slimpay.models.payment import SlimpayClient


def _get_from_doc_mock(doc, method_name):
    """ Dummy mock for SimplayClient.get_from_doc that returns a hard-coded
    hal document for the requested method name, whatever the specified doc.
    """
    return {'get-mandate': {'id': 'my-mandate-id'},
            'get-bank-account': {'institutionName': 'my-bank',
                                 'iban': 'my-iban'},
            }[method_name]


class MockedSlimpayMixin(object):

    def setup_mocks(self):
        self._patchers = []
        # Mock SlimpayClient
        self._start_patcher(
            patch('odoo.addons.account_payment_slimpay.models.'
                  'slimpay_utils.get_client'))
        # Mock its "get" and "get_from_doc" methods (to ease their config)
        self.fake_get = self._start_patcher(patch.object(SlimpayClient, 'get'))
        self._start_patcher(patch.object(
            SlimpayClient, 'get_from_doc', side_effect=_get_from_doc_mock))
        # Mock approval_url
        self._start_patcher(patch.object(
            SlimpayClient, 'approval_url',
            side_effect=lambda tx_ref, *args, **kw: tx_ref))
        self.slimpay = self.env.ref(
            'account_payment_slimpay.payment_acquirer_slimpay')
        # Stop patchers in case of a test exception or normal termination
        for patcher in self._patchers:
            self.addCleanup(patcher.stop)

    def _start_patcher(self, patcher):
        self._patchers.append(patcher)
        return patcher.start()
