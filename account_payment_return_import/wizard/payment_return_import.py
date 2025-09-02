# Copyright 2016 Tecnativa - Carlos Dauden
# Copyright 2016 Tecnativa - Pedro M. Baeza
# Copyright 2018 Tecnativa - Luis M. Ontalba
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from io import BytesIO
from zipfile import BadZipfile, ZipFile  # BadZipFile in Python >= 3.2

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base_iban.models.res_partner_bank import pretty_iban

from .base_parser import BaseParser

_logger = logging.getLogger(__name__)


class PaymentReturnImport(models.TransientModel):
    _name = "payment.return.import"
    _description = "Import Payment Return"

    def _compute_hide_journal_field(self):
        """Return False if the journal_id can't be provided by the parsed
        file and must be provided by the wizard."""
        self.hide_journal_field = True

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        help="Accounting journal related to the bank payment return you're "
        "importing. It has be be manually chosen for payment return formats "
        "which doesn't allow automatic journal detection.",
    )
    hide_journal_field = fields.Boolean(
        string="Hide the journal field in the view",
        compute="_compute_hide_journal_field",
    )
    data_file = fields.Binary(
        string="Payment Return File",
        required=True,
        help="Get you bank payment returns in electronic format from your "
        "bank and select them here.",
    )
    match_after_import = fields.Boolean(default=True)

    def import_file(self):
        """Process the file chosen in the wizard, create bank payment return(s)
        and go to reconciliation."""
        self.ensure_one()
        data_file = base64.b64decode(self.data_file)
        payment_returns, notifications = self.with_context(
            active_id=self.id
        )._import_file(data_file)
        xmlid = "account_payment_return.payment_return_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        if self.match_after_import:
            payment_returns.button_match()
        if len(payment_returns) != 1:
            action["domain"] = f"[('id', 'in', {payment_returns.ids})]"
        else:
            form_view = self.env.ref("account_payment_return.payment_return_form_view")
            action.update(
                {
                    "views": [(form_view.id, "form")],
                    "res_id": payment_returns.id,
                    "context": {"notifications": notifications},
                }
            )
        return action

    @api.model
    def _parse_all_files(self, data_file):
        """Parse one or multiple files from zip-file.

        :param data_file: Decoded raw content of the file
        :return: List of payment returns dictionaries for further processing.
        """
        payment_return_raw_list = []
        files = [data_file]
        try:
            with ZipFile(BytesIO(data_file), "r") as archive:
                files = [
                    archive.read(filename)
                    for filename in archive.namelist()
                    if not filename.endswith("/")
                ]
        except BadZipfile:
            _logger.info("Invalid Zip file")
        # Parse the file(s)
        for import_file in files:
            # The appropriate implementation module(s) returns the payment
            # returns. We support a list of dictionaries or a simple
            # dictionary.

            # Actually we don't care wether all the files have the
            # same format.
            vals = self._parse_file(import_file)
            if isinstance(vals, list):
                payment_return_raw_list += vals
            else:
                payment_return_raw_list.append(vals)
        return payment_return_raw_list

    @api.model
    def _import_file(self, data_file):
        """Create bank payment return(s) from file."""
        # The appropriate implementation module returns the required data
        payment_returns = self.env["payment.return"]
        notifications = []
        payment_return_raw_list = self._parse_all_files(data_file)
        # Check raw data:
        self._check_parsed_data(payment_return_raw_list)
        # Import all payment returns:
        for payret_vals in payment_return_raw_list:
            payret_vals = self._complete_payment_return(payret_vals)
            payment_return, new_notifications = self._create_payment_return(payret_vals)
            if payment_return:
                payment_returns += payment_return
            notifications.extend(new_notifications)
        if not payment_returns:
            raise UserError(self.env._("You have already imported this file."))
        return payment_returns, notifications

    @api.model
    def _parse_file(self, data_file):
        """Each module adding a file support must extends this method. It
        processes the file if it can, returns super otherwise, resulting in a
        chain of responsability.
        This method parses the given file and returns the data required by
        the bank payment return import process, as specified below.
        - bank payment returns data: list of dict containing (optional
                                items marked by o) :
            -o account number: string (e.g: 'BE1234567890')
                The number of the bank account which the payment return
                belongs to
            - 'name': string (e.g: '000000123')
            - 'date': date (e.g: 2013-06-26)
            - 'transactions': list of dict containing :
                - 'amount': float
                - 'unique_import_id': string
                -o 'concept': string
                -o 'reason_code': string
                -o 'reason': string
                -o 'partner_name': string
                -o 'reference': string
        """
        parser = BaseParser()
        try:
            return parser.parse(data_file)
        except Exception:
            raise UserError(
                self.env._(
                    "Could not make sense of the given file.\n"
                    "Did you install the module to support this type of file?"
                )
            ) from Exception

    @api.model
    def _check_parsed_data(self, payment_returns):
        """Basic and structural verifications"""
        if not payment_returns:
            raise UserError(self.env._("This file doesn't contain any payment return."))
        for payret_vals in payment_returns:
            if payret_vals.get("transactions"):
                return
        # If we get here, no transaction was found:
        raise UserError(self.env._("This file doesn't contain any transaction."))

    @api.model
    def _find_bank_account_id(self, account_number):
        """Get res.partner.bank ID"""
        bank_account_id = None
        if account_number and len(account_number) > 4:
            iban_number = pretty_iban(account_number)
            bank_account = self.env["res.partner.bank"].search(
                [("acc_number", "=", iban_number)], limit=1
            )
            if bank_account:
                bank_account_id = bank_account.id
        return bank_account_id

    @api.model
    def _get_journal(self, bank_account_id):
        """Find the journal"""
        bank_model = self.env["res.partner.bank"]
        # Find the journal from context, wizard or bank account
        journal_id = self.env.context.get("journal_id") or self.journal_id.id
        if bank_account_id:
            bank_account = bank_model.browse(bank_account_id)
            if journal_id:
                if (
                    bank_account.journal_id
                    and journal_id not in bank_account.journal_id.ids
                ):
                    raise UserError(
                        self.env._(
                            "The account of this payment return is linked to "
                            "another journal."
                        )
                    )
                if not bank_account.journal_id:
                    bank_model.write({"journal_id": journal_id})
            elif bank_account.journal_id:
                journal_id = bank_account.journal_id.id
        return journal_id

    @api.model
    def _complete_payment_return(self, payret_vals):
        """Complete payment return from information passed."""
        account_number = payret_vals.pop("account_number")
        if not payret_vals.get("journal_id"):
            bank_account_id = self._find_bank_account_id(account_number)
            if not bank_account_id and account_number:
                raise UserError(
                    self.env._("Can not find the account number %s.") % account_number
                )
            payret_vals.update(
                {
                    "imported_bank_account_id": bank_account_id,
                    "journal_id": self._get_journal(bank_account_id),
                }
            )
            # By now journal and account_number must be known
            if not payret_vals["journal_id"]:
                raise UserError(self.env._("Can not determine journal for import."))
        for line_vals in payret_vals["transactions"]:
            unique_import_id = line_vals.get("unique_import_id", False)
            if unique_import_id:
                line_vals["unique_import_id"] = (
                    account_number and (account_number + "-") or ""
                ) + unique_import_id
            if not line_vals.get("reason"):
                reason = self.env["payment.return.reason"].name_search(
                    line_vals.pop("reason_code")
                )
                if reason:
                    line_vals["reason_id"] = reason[0][0]
        return payret_vals

    @api.model
    def _create_payment_return(self, payret_vals):
        """Create bank payment return from imported values, filtering out
        already imported transactions, and return data used by the
        reconciliation widget
        """
        pr_model = self.env["payment.return"]
        prl_model = self.env["payment.return.line"]
        # Filter out already imported transactions and create payment return
        ignored_line_ids = []
        filtered_st_lines = []
        for line_vals in payret_vals["transactions"]:
            unique_id = (
                "unique_import_id" in line_vals and line_vals["unique_import_id"]
            )
            if not unique_id or not bool(
                prl_model.sudo().search([("unique_import_id", "=", unique_id)], limit=1)
            ):
                filtered_st_lines.append(line_vals)
            else:
                ignored_line_ids.append(unique_id)
        payment_return = pr_model.browse()
        if len(filtered_st_lines) > 0:
            # Remove values that won't be used to create records
            payret_vals.pop("transactions", None)
            for line_vals in filtered_st_lines:
                line_vals.pop("account_number", None)
            # Create the payment return
            payret_vals["line_ids"] = [[0, False, line] for line in filtered_st_lines]
            payment_return = pr_model.create(payret_vals)
        # Prepare import feedback
        notifications = []
        num_ignored = len(ignored_line_ids)
        if num_ignored > 0:
            notifications += [
                {
                    "type": "warning",
                    "message": self.env._(
                        "%d transactions had already been imported and were ignored."
                    )
                    % num_ignored
                    if num_ignored > 1
                    else self.env._(
                        "1 transaction had already been imported and was ignored."
                    ),
                    "details": {
                        "name": self.env._("Already imported items"),
                        "model": "payment.return.line",
                        "ids": prl_model.search(
                            [("unique_import_id", "in", ignored_line_ids)]
                        ).ids,
                    },
                }
            ]
        return payment_return, notifications
