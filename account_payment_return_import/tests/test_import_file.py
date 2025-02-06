# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Luis M. Ontalba
# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import fields
from odoo.tools.misc import file_open, file_path

from odoo.addons.base.tests.common import BaseCommon

_logger = logging.getLogger(__name__)


class TestPaymentReturnFile(BaseCommon):
    """Check whether payment returns with transactions correctly imported.

    No actual tests are done in this class, implementations are in
    subclasses in actual import modules.
    """

    def _test_transaction(
        self, return_obj, reference=False, returned_amount=False, reason_add_info=False
    ):
        """Check whether transaction with attributes passed was created.

        Actually this method also tests whether automatic creation of
        partner bank accounts is working.
        """
        transaction_model = self.env["payment.return.line"]
        domain = [("return_id", "=", return_obj.id)]
        if returned_amount:
            domain.append(("amount", "=", returned_amount))
        if reference:
            domain.append(("reference", "=", reference))
        if reason_add_info:
            domain.append(("reason_additional_information", "=", reason_add_info))
        ids = transaction_model.search(domain)
        if not ids:
            # We will get assertion error, but to solve we need to see
            # what transactions have been added:
            self.cr.execute(
                "SELECT reference, amount "
                "FROM payment_return_line "
                "WHERE return_id=%s",
                (return_obj.id,),
            )
            _logger.error(f"Transaction not found in {self.cr.fetchall()}")
        self.assertTrue(ids, f"Transaction {domain} not found after parse.")

    def _test_return_import(
        self,
        module_name,
        file_name,
        return_name,
        local_account=False,
        date=False,
        transactions=None,
    ):
        """Test correct creation of single return."""
        import_model = self.env["payment.return.import"]
        return_model = self.env["payment.return"]
        return_path = file_path(module_name + "/tests/test_files/" + file_name)
        return_file = base64.b64encode(file_open(return_path, "rb").read())
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
                journal_id, f"Bank account {local_account} has not journal assigned"
            )
        ids = return_model.search([("name", "=", return_name)])
        self.assertTrue(ids, f"Payment return {return_name} not found after parse.")
        return_obj = ids[0]
        if date:
            self.assertEqual(
                fields.Date.to_string(return_obj.date),
                date,
                f"Date {fields.Date.to_string(return_obj.date)}\
                not equal to expected {date}",
            )
        if transactions:
            for transaction in transactions:
                self._test_transaction(return_obj, **transaction)
