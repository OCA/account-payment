# -*- coding: utf-8 -*-
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp.tests.common import TransactionCase
from openerp.modules.module import get_module_resource


_logger = logging.getLogger(__name__)


class TestPaymentReturnFile(TransactionCase):
    """Check whether payment returns with transactions correctly imported.

    No actual tests are done in this class, implementations are in
    subclasses in actual import modules.
    """

    def _test_transaction(
            self, return_obj, reference=False, returned_amount=False):
        """Check whether transaction with attributes passed was created.

        Actually this method also tests whether automatic creation of
        partner bank accounts is working.
        """
        transaction_model = self.env['payment.return.line']
        domain = [('return_id', '=', return_obj.id)]
        if returned_amount:
            domain.append(('amount', '=', returned_amount))
        if reference:
            domain.append(('reference', '=', reference))
        ids = transaction_model.search(domain)
        if not ids:
            # We will get assertion error, but to solve we need to see
            # what transactions have been added:
            self.cr.execute(
                "select reference, amount"
                " from payment_return_line"
                " where return_id=%d" % return_obj.id)
            _logger.error(
                "Transaction not found in %s" %
                str(self.cr.fetchall())
            )
        self.assertTrue(
            ids,
            'Transaction %s not found after parse.' % str(domain)
        )

    def _test_return_import(
            self, module_name, file_name, return_name, local_account=False,
            date=False, transactions=None):
        """Test correct creation of single return."""
        import_model = self.env['payment.return.import']
        return_model = self.env['payment.return']
        return_path = get_module_resource(
            module_name,
            'test_files',
            file_name
        )
        return_file = open(
            return_path, 'rb').read().encode('base64')
        bank_return_id = import_model.create(
            dict(
                data_file=return_file,
            )
        )
        bank_return_id.import_file()
        if local_account:
            bank_account_id = import_model._find_bank_account_id(local_account)
            journal_id = import_model._get_journal(bank_account_id)
            self.assertTrue(
                journal_id,
                'Bank account %s has not journal assigned' % local_account
            )
        ids = return_model.search([('name', '=', return_name)])
        self.assertTrue(
            ids,
            'Payment return %s not found after parse.' % return_name
        )
        return_obj = ids[0]
        if date:
            self.assertEqual(
                return_obj.date, date,
                'Date %s not equal to expected %s' %
                (return_obj.date, date)
            )
        if transactions:
            for transaction in transactions:
                self._test_transaction(return_obj, **transaction)
