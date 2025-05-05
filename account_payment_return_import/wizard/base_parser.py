# Copyright 2017 Tecnativa - David Vidal
# Copyright 2018 Tecnativa - Luis M. Ontalba
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
from io import StringIO

from odoo.exceptions import UserError


class BaseParser:
    """Base parser to allow csv imports."""

    def parse_payment_return(self, row):
        """Parse a single payment return row"""
        transaction = {}
        if row["unique_import_id"]:
            transaction.update(
                unique_import_id=row["unique_import_id"],
                amount=row["amount"] or 0.0,
                concept=row["concept"] or "",
                reason_code=row["reason_code"] or "",
                partner_name=row["partner_name"] or "",
                reference=row["reference"] or "",
            )
        return {
            "name": row["name"],
            "date": row["date"],
            "account_number": row["account_number"],
            "transactions": [transaction],
        }

    def parse(self, data):
        """Dummy csv parse"""
        try:
            data = StringIO(data.decode())
            reader = csv.DictReader(data)
            payment_returns = []
            for row in reader:
                payment_return = self.parse_payment_return(row)
                if len(payment_return["transactions"]):
                    payment_returns.append(payment_return)
        except Exception:
            raise UserError(self.env._("Couldn't load file data")) from Exception
        return payment_returns
