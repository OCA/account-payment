# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# Copyright 2018 Minorisa, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestAccountPartnerReconcile(TransactionCase):
    """
        Tests for Account Partner Reconcile.
    """

    def setUp(self):
        super(TestAccountPartnerReconcile, self).setUp()

        self.partner1 = self.env.ref('base.res_partner_1')

    def test_account_partner_reconcile(self):
        res = self.partner1.action_open_reconcile()

        # assertDictContainsSubset is deprecated in Python <3.2
        expected = {
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
        }
        self.assertDictEqual(
            expected, {k: v for k, v in res.items() if k in expected},
            'There was an error and the manual_reconciliation_view couldn\'t be opened.')

        expected = {
            'partner_ids': self.partner1.ids,
            'show_mode_selector': True,
        }
        self.assertDictEqual(
            expected, {k: v for k, v in res['context'].items() if k in expected},
            'There was an error and the manual_reconciliation_view couldn\'t be opened.')
