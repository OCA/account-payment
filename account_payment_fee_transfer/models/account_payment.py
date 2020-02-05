# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    fee_transfer = fields.Monetary(
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        help="Fee being charged into the account of 'Deduct From'",
    )
    deduct_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Deduct From",
        domain="[('id', 'in', [journal_id, destination_journal_id])]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.constrains("fee_transfer")
    def _check_fee_transfer(self):
        if self.fee_transfer < 0:
            raise ValidationError(_("amount fee transfer cannot be negative."))

    def _prepare_payment_moves(self):
        """ Update fee transfer and balance by creating a list of python dictionary

        Example 1: Transfer, BANK1 -> BANK2 (fee on BANK1):

        Account             | Debit     | Credit
        =========================================================
        Journal Entry 1
        ---------------
        BANK1               |           |   1000.0
        BANK1               |           |     10.0        --> Fee
        ACCOUNT FEE         |     10.0  |
        TRANSFER            |   1000.0  |

        Journal Entry 2
        ---------------
        TRANSFER            |           |   1000.0
        BANK2               |   1000.0  |

        Example 2: Transfer, BANK1 -> BANK2 (fee on BANK2):

        Account             | Debit     | Credit
        =========================================================
        Journal Entry 1
        ---------------
        BANK1               |           |   1000.0
        TRANSFER            |   1000.0  |

        Journal Entry 2
        ---------------
        TRANSFER            |           |   1000.0
        BANK2               |   1000.0  |
        ACCOUNT FEE         |     10.0  |
        BANK2               |           |     10.0        --> Fee

        Example 3: Transfer, BANK1 -> BANK3 (USD) (fee on BANK1):

        Account             | Debit     | Credit     | Amount Currency
        ===============================================================
        Journal Entry 1
        ---------------
        BANK1               |           |   1000.0   |
        BANK1               |           |     10.0   |                --> Fee
        ACCOUNT FEE         |     10.0  |            |
        TRANSFER            |   1000.0  |            |

        Journal Entry 2
        ---------------
        TRANSFER            |           |   1000.0   |
        BANK3               |   1000.0  |            |   1283.4

        Example 4: Transfer, BANK1 -> BANK3 (USD) (fee on BANK3):

        Account             | Debit     | Credit     | Amount Currency
        ===============================================================
        Journal Entry 1
        ---------------
        BANK1               |           |   1000.0   |
        TRANSFER            |   1000.0  |            |

        Journal Entry 2
        ---------------
        TRANSFER            |           |   1000.0   |
        ACCOUNT FEE         |     10.0  |            |
        BANK3               |           |     10.0   |    -12.83       --> Fee
        BANK3               |   1000.0  |            |   1283.40

        :return: A list of Python dictionary to be passed to env['account.move'].create.
        """
        res = super(AccountPayment, self)._prepare_payment_moves()
        for payment in self:
            company_currency = payment.company_id.currency_id
            deduct_currency = payment.deduct_journal_id.currency_id
            if payment.payment_type != "transfer" or payment.fee_transfer == 0.0:
                continue
            for move in res:
                journal_id = move.get("journal_id", False)
                lines = move.get("line_ids")
                # fee_transfer_name = _('Fee transfer from %s') \
                #     % payment.deduct_journal_id.name

                # Manage currency.
                if payment.currency_id == company_currency:
                    # Single-currency.
                    balance = payment.fee_transfer
                    currency_id = False
                else:
                    # Multi-currencies.
                    balance = payment.currency_id._convert(
                        payment.fee_transfer,
                        company_currency,
                        payment.company_id,
                        payment.payment_date,
                    )
                    currency_id = payment.currency_id.id

                # Add fee transfer in journal deduct.
                if journal_id == payment.deduct_journal_id.id:
                    credit_account_id = (
                        payment.deduct_journal_id.default_credit_account_id.id
                    )
                    # case : Deduct fee transfer from multi currency
                    if payment.currency_id != deduct_currency:
                        # convert main to currency
                        fee_transfer = payment.currency_id._convert(
                            balance,
                            deduct_currency,
                            payment.company_id,
                            payment.payment_date,
                        )
                        lines.append(
                            (
                                0,
                                0,
                                {
                                    "name": payment.writeoff_label,
                                    "amount_currency": -fee_transfer
                                    if deduct_currency
                                    else 0.0,
                                    "currency_id": deduct_currency.id,
                                    "debit": 0.0,
                                    "credit": balance,
                                    "date_maturity": payment.payment_date,
                                    "partner_id": payment.partner_id.id,
                                    "account_id": credit_account_id,
                                    "payment_id": payment.id,
                                },
                            )
                        )
                    else:
                        lines.append(
                            (
                                0,
                                0,
                                {
                                    "name": payment.writeoff_label,
                                    "amount_currency": -payment.fee_transfer
                                    if currency_id
                                    else 0.0,
                                    "currency_id": currency_id,
                                    "debit": 0.0,
                                    "credit": balance,
                                    "date_maturity": payment.payment_date,
                                    "partner_id": payment.partner_id.id,
                                    "account_id": credit_account_id,
                                    "payment_id": payment.id,
                                },
                            )
                        )
                    lines.append(
                        (
                            0,
                            0,
                            {
                                "name": payment.writeoff_label,
                                "amount_currency": payment.fee_transfer
                                if currency_id
                                else 0.0,
                                "currency_id": currency_id,
                                "debit": balance,
                                "credit": 0.0,
                                "date_maturity": payment.payment_date,
                                "partner_id": payment.partner_id.id,
                                "account_id": payment.writeoff_account_id.id,
                                "payment_id": payment.id,
                            },
                        )
                    )
        return res
