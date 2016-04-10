# -*- coding: utf-8 -*-
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


class ReturnTransaction(dict):
    """Single transaction that is part of a bank payment_return."""

    @property
    def value_date(self):
        """property getter"""
        return self['date']

    @value_date.setter
    def value_date(self, value_date):
        """property setter"""
        self['date'] = value_date

    @property
    def returned_amount(self):
        """property getter"""
        return self['amount']

    @returned_amount.setter
    def returned_amount(self, returned_amount):
        """property setter"""
        self['amount'] = returned_amount

    @property
    def reference(self):
        """property getter"""
        return self['reference']

    @reference.setter
    def reference(self, reference):
        """property setter"""
        self['reference'] = reference

    @property
    def concept(self):
        """property getter"""
        return self['concept']

    @concept.setter
    def concept(self, concept):
        """property setter"""
        self['concept'] = concept

    @property
    def remote_owner(self):
        """property getter"""
        return self['partner_name']

    @remote_owner.setter
    def remote_owner(self, remote_owner):
        """property setter"""
        self['partner_name'] = remote_owner

    @property
    def remote_account(self):
        """property getter"""
        return self['account_number']

    @remote_account.setter
    def remote_account(self, remote_account):
        """property setter"""
        self['account_number'] = remote_account

    @property
    def reason_code(self):
        return self['reason_code']

    @reason_code.setter
    def reason_code(self, reason_code):
        self['reason_code'] = reason_code

    @property
    def reason(self):
        return self['reason']

    @reason.setter
    def reason(self, reason):
        self['reason'] = reason

    def __init__(self):
        """Define and initialize attributes.

        Not all attributes are already used in the actual import.
        """
        super(ReturnTransaction, self).__init__()
        self.concept = False
        self.reason_code = False
        self.reason = ''
        self.remote_account = False  # The account of the other party
        self.name = ''
        self.reference = False  # end to end reference for transactions
        self.move_line_ids = False  # related move with original ref
        self.remote_owner = False  # name of the other party
        self.remote_bank_bic = False  # bic of other party's bank
        self.value_date = False  # Date at which the creditor requests that the
        # amount of money is to be collected from the debtor.
        self.error_message = False  # error message for interaction with user
        self.data = ''  # Raw data from which the transaction has been parsed


class PaymentReturn(dict):
    """A bank payment_return groups data about several bank transactions."""

    @property
    def payment_return_name(self):
        """property getter"""
        return self['name']

    def _set_transaction_ids(self):
        """Set transaction ids to payment_return_name with sequence-number."""
        subno = 0
        for transaction in self['transactions']:
            subno += 1
            transaction['unique_import_id'] = (
                self.payment_return_name + str(subno).zfill(4))

    @payment_return_name.setter
    def payment_return_name(self, payment_return_name):
        """property setter"""
        self['name'] = payment_return_name
        self._set_transaction_ids()

    @property
    def date(self):
        """property getter"""
        return self['date']

    @date.setter
    def date(self, date):
        """property setter"""
        self['date'] = date

    @property
    def local_account(self):
        """property getter"""
        return self['account_number']

    @local_account.setter
    def local_account(self, local_account):
        """property setter"""
        self['account_number'] = local_account

    def create_transaction(self):
        """Create and append transaction.
        This should only be called after payment_return_name has been set,
        because payment_return_name will become part of the unique
        transaction_id.
        """
        transaction = ReturnTransaction()
        self['transactions'].append(transaction)
        # Fill default id, but might be overruled
        transaction['unique_import_id'] = (
            self.payment_return_name + str(len(self['transactions'])).zfill(4))
        return transaction

    def __init__(self):
        super(PaymentReturn, self).__init__()
        self['transactions'] = []
        self.payment_return_name = ''
        self.date = False
        self.local_account = False
