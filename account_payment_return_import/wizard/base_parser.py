# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# Copyright 2018 Tecnativa - Luis M. Ontalba
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import UserError
import csv
from io import StringIO


class BaseParser(object):
    """ Base parser to allow csv imports. """

    def parse_payment_return(self, row):
        """Parse a single payment return row"""
        payment_return = {}
        payment_return['name'] = row['name']
        payment_return['date'] = row['date']
        payment_return['account_number'] = row['account_number']
        transaction = {}
        if row['unique_import_id']:
            transaction['unique_import_id'] = row['unique_import_id']
            transaction['amount'] = row['amount'] or 0.0
            transaction['concept'] = row['concept'] or ''
            transaction['reason_code'] = row['reason_code'] or ''
            transaction['partner_name'] = row['partner_name'] or ''
            transaction['reference'] = row['reference'] or ''
        payment_return['transactions'] = [transaction]
        return payment_return

    def parse(self, data):
        """Dummy csv parse"""
        try:
            data = StringIO(data.decode())
            reader = csv.DictReader(data)
            payment_returns = []
            for row in reader:
                payment_return = self.parse_payment_return(row)
                if len(payment_return['transactions']):
                    payment_returns.append(payment_return)
        except Exception:
            raise UserError(_("Couldn't load file data"))
        return payment_returns
