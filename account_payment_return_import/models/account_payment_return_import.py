# -*- coding: utf-8 -*-
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Framework for importing payment return files."""
import logging
import base64
from StringIO import StringIO
from zipfile import ZipFile, BadZipfile  # BadZipFile in Python >= 3.2

from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError, RedirectWarning

from openerp.addons.base_iban.base_iban import _pretty_iban

_logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class PaymentReturnLine(models.Model):
    """Extend model payment.return.line."""
    # pylint: disable=too-many-public-methods
    _inherit = 'payment.return.line'

    # Ensure transactions can be imported only once (if the import format
    # provides unique transaction ids)
    unique_import_id = fields.Char('Import ID', readonly=True, copy=False)

    _sql_constraints = [
        ('unique_import_id',
         'unique (unique_import_id)',
         'A bank account transactions can be imported only once !')
    ]


class PaymentReturnImport(models.TransientModel):
    _name = 'payment.return.import'
    _description = 'Import Payment Return'

    @api.model
    def _get_hide_journal_field(self):
        """ Return False if the journal_id can't be provided by the parsed
        file and must be provided by the wizard."""
        # pylint: disable=no-self-use
        return True

    journal_id = fields.Many2one(
        'account.journal', string='Journal',
        help='Accounting journal related to the bank payment return you\'re '
        'importing. It has be be manually chosen for payment return formats '
        'which doesn\'t allow automatic journal detection.')
    hide_journal_field = fields.Boolean(
        string='Hide the journal field in the view',
        compute='_get_hide_journal_field')
    data_file = fields.Binary(
        'Payment Return File', required=True,
        help='Get you bank payment returns in electronic format from your '
             'bank and select them here.')

    @api.multi
    def import_file(self):
        """Process the file chosen in the wizard, create bank payment return(s)
        and go to reconciliation."""
        self.ensure_one()
        data_file = base64.b64decode(self.data_file)
        # pylint: disable=protected-access
        payment_return_ids, notifications = self.with_context(
            active_id=self.id  # pylint: disable=no-member
        )._import_file(data_file)
        # dispatch to reconciliation interface
        result = self.env.ref(
            'account_payment_return.payment_return_action').read()[0]
        if len(payment_return_ids) != 1:
            result['domain'] = "[('id', 'in', %s)]" % payment_return_ids
        else:
            res = self.env.ref(
                'account_payment_return.payment_return_form_view', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = payment_return_ids[0]
        return result

    @api.model
    def _parse_all_files(self, data_file):
        """Parse one file or multiple files from zip-file.
        Return array of payment returns for further processing.
        """
        payment_returns = []
        files = [data_file]
        try:
            with ZipFile(StringIO(data_file), 'r') as archive:
                files = [
                    archive.read(filename) for filename in archive.namelist()
                    if not filename.endswith('/')
                    ]
        except BadZipfile:
            pass
        # Parse the file(s)
        for import_file in files:
            # The appropriate implementation module(s) returns the payment
            # returns. Actually we don't care wether all the files have the
            # same format.
            payment_returns += self._parse_file(import_file)
        return payment_returns

    @api.model
    def _import_file(self, data_file):
        """ Create bank payment return(s) from file."""
        # The appropriate implementation module returns the required data
        payment_return_ids = []
        notifications = []
        payment_returns = self._parse_all_files(data_file)
        # Check raw data:
        self._check_parsed_data(payment_returns)
        # Import all payment returns:
        for payret_vals in payment_returns:
            (payment_return_id, new_notifications) = (
                self._import_payment_return(payret_vals))
            if payment_return_id:
                payment_return_ids.append(payment_return_id)
            notifications.extend(new_notifications)
        if len(payment_return_ids) == 0:
            raise UserError(_('You have already imported that file.'))
        return payment_return_ids, notifications

    @api.model
    def _import_payment_return(self, payret_vals):
        """Import a single bank payment return.

        Return ids of created payment returns and notifications.
        """
        account_number = payret_vals.pop('account_number')
        bank_account_id = self._find_bank_account_id(account_number)
        if not bank_account_id and account_number:
            raise UserError(
                _('Can not find the account number %s.') % account_number
            )
        # Find the bank journal
        journal_id = self._get_journal(bank_account_id)
        # By now journal and account_number must be known
        if not journal_id:
            raise UserError(_('Can not determine journal for import.'))
        # Prepare payment return data to be used for payment returns creation
        payret_vals = self._complete_payment_return(
            payret_vals, journal_id, account_number)
        # Create the bank payret_vals
        return self._create_payment_return(payret_vals)

    @api.model
    def _parse_file(self, data_file):
        # pylint: disable=no-self-use
        # pylint: disable=unused-argument
        """ Each module adding a file support must extends this method. It
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
        raise UserError(_(
            'Could not make sense of the given file.\n'
            'Did you install the module to support this type of file?'
        ))

    @api.model
    def _check_parsed_data(self, payment_returns):
        # pylint: disable=no-self-use
        """ Basic and structural verifications """
        if len(payment_returns) == 0:
            raise UserError(_(
                'This file doesn\'t contain any payment return.'))
        for payret_vals in payment_returns:
            if 'transactions' in payret_vals and payret_vals['transactions']:
                return
        # If we get here, no transaction was found:
        raise UserError(_('This file doesn\'t contain any transaction.'))

    @api.model
    def _find_bank_account_id(self, account_number):
        """ Get res.partner.bank ID """
        bank_account_id = None
        if account_number and len(account_number) > 4:
            iban_number = _pretty_iban(account_number)
            bank_account_ids = self.env['res.partner.bank'].search(
                [('acc_number', '=', iban_number)], limit=1)
            if bank_account_ids:
                bank_account_id = bank_account_ids[0].id
        return bank_account_id

    @api.model
    def _get_journal(self, bank_account_id):
        """ Find the journal """
        bank_model = self.env['res.partner.bank']
        # Find the journal from context, wizard or bank account
        journal_id = self.env.context.get('journal_id') or self.journal_id.id
        if bank_account_id:
            bank_account = bank_model.browse(bank_account_id)
            if journal_id:
                if (bank_account.journal_id.id and
                        bank_account.journal_id.id != journal_id):
                    raise UserError(
                        _('The account of this payment return is linked to '
                          'another journal.'))
                if not bank_account.journal_id.id:
                    bank_model.write({'journal_id': journal_id})
            else:
                if bank_account.journal_id.id:
                    journal_id = bank_account.journal_id.id
        return journal_id

    @api.model
    def _complete_payment_return(
            self, payret_vals, journal_id, account_number):
        """Complete payment return from information passed."""
        payret_vals['journal_id'] = journal_id
        for line_vals in payret_vals['transactions']:
            unique_import_id = line_vals.get('unique_import_id', False)
            if unique_import_id:
                line_vals['unique_import_id'] = (
                    (account_number and account_number + '-' or '') +
                    unique_import_id
                )
            if not line_vals.get('reason'):
                reason = self.env['payment.return.reason'].name_search(
                    line_vals.pop('reason_code'))
                if reason:
                    line_vals['reason'] = reason[0][0]
        if 'date' in payret_vals and 'period_id' not in payret_vals:
            # if the parser found a date but didn't set a period for this date,
            # do this now
            try:
                payret_vals['period_id'] =\
                    self.env['account.period']\
                        .with_context(account_period_prefer_normal=True)\
                        .find(dt=payret_vals['date']).id
            except RedirectWarning:
                # if there's no period for the date, ignore resulting exception
                pass
        return payret_vals

    @api.model
    def _create_payment_return(self, payret_vals):
        """ Create bank payment return from imported values, filtering out
        already imported transactions, and return data used by the
        reconciliation widget
        """
        pr_model = self.env['payment.return']
        prl_model = self.env['payment.return.line']
        # Filter out already imported transactions and create payment return
        ignored_line_ids = []
        filtered_st_lines = []
        for line_vals in payret_vals['transactions']:
            unique_id = (
                'unique_import_id' in line_vals and
                line_vals['unique_import_id']
            )
            if not unique_id or not bool(prl_model.sudo().search(
                    [('unique_import_id', '=', unique_id)], limit=1)):
                filtered_st_lines.append(line_vals)
            else:
                ignored_line_ids.append(unique_id)
        payment_return_id = False
        if len(filtered_st_lines) > 0:
            # Remove values that won't be used to create records
            payret_vals.pop('transactions', None)
            for line_vals in filtered_st_lines:
                line_vals.pop('account_number', None)
            # Create the payment return
            payret_vals['line_ids'] = [
                [0, False, line] for line in filtered_st_lines]
            payment_return_id = pr_model.create(payret_vals).id
        # Prepare import feedback
        notifications = []
        num_ignored = len(ignored_line_ids)
        if num_ignored > 0:
            notifications += [{
                'type': 'warning',
                'message':
                    _("%d transactions had already been imported and "
                      "were ignored.") % num_ignored
                    if num_ignored > 1
                    else _("1 transaction had already been imported and "
                           "was ignored."),
                'details': {
                    'name': _('Already imported items'),
                    'model': 'payment.return.line',
                    'ids': prl_model.search(
                        [('unique_import_id', 'in', ignored_line_ids)]).ids}
            }]
        return payment_return_id, notifications
