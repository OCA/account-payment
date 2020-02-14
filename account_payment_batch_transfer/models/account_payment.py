# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    use_batch_transfer = fields.Boolean(
        readonly=True, states={"draft": [("readonly", False)]}
    )
    batch_transfer_ids = fields.One2many(
        comodel_name="account.payment.batch.transfer",
        inverse_name="payment_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="create batch transfer and support fee",
    )

    @api.onchange("use_batch_transfer")
    def onchange_batch_transfer(self):
        if self.use_batch_transfer:
            self.fee_transfer = 0.0

    def post(self):
        for rec in self:
            if rec.use_batch_transfer:
                if rec.amount != sum(rec.batch_transfer_ids.mapped("amount")):
                    raise ValidationError(
                        _("Payment Amount and Total Transaction are not equal!")
                    )
                if sum(rec.batch_transfer_ids.mapped("amount")) != 0.0 and not (
                    rec.writeoff_account_id and rec.deduct_journal_id
                ):
                    raise ValidationError(
                        _("You must select Fee Account and Deduct From.")
                    )
        return super().post()

    def _prepare_payment_moves(self):
        """ Update batch transfer by creating a list of python dictionary

        Example 1: Batch Transfer 2 transaction, BANK1 -> BANK2 (fee on BANK1):

        Account             | Debit     | Credit
        =========================================================
        Journal Entry 1
        ---------------
        BANK1               |           |    800.0        --> Batch1
        BANK1               |           |    200.0        --> Batch2
        BANK1               |           |     80.0        --> Fee1
        ACCOUNT FEE 1       |     80.0  |
        BANK1               |           |     20.0        --> Fee2
        ACCOUNT FEE 2       |     20.0  |
        TRANSFER            |   1000.0  |

        Journal Entry 2
        ---------------
        TRANSFER            |           |   1000.0
        BANK2               |    800.0  |
        BANK2               |    200.0  |

        Example 2: Batch Transfer 2 transaction, BANK1 -> BANK2 (fee on BANK2):

        Account             | Debit     | Credit
        =========================================================
        Journal Entry 1
        ---------------
        BANK1               |           |    800.0
        BANK1               |           |    200.0
        TRANSFER            |   1000.0  |

        Journal Entry 2
        ---------------
        TRANSFER            |           |   1000.0
        BANK2               |    800.0  |
        BANK2               |    200.0  |
        ACCOUNT FEE 1       |     10.0  |
        BANK2               |           |     10.0        --> Fee
        ACCOUNT FEE 2       |     10.0  |
        BANK2               |           |     10.0        --> Fee

        :return: A list of Python dictionary to be passed to env['account.move'].create.
        """
        res = super(AccountPayment, self)._prepare_payment_moves()
        for payment in self:
            company_currency = payment.company_id.currency_id
            if payment.payment_type != "transfer" or not payment.use_batch_transfer:
                continue
            for move in res:
                journal_id = move.get("journal_id", False)
                lines = move.get("line_ids")
                if journal_id == payment.journal_id.id:
                    line_name = (
                        _("Transfer to %s") % payment.destination_journal_id.name
                    )
                    account_id = payment.journal_id.default_debit_account_id.id
                    sign = 1
                else:
                    line_name = _("Transfer from %s") % payment.journal_id.name
                    account_id = (
                        payment.destination_journal_id.default_debit_account_id.id
                    )
                    sign = -1
                # delete lines to batch transfer
                del lines[:]

                for line in payment.batch_transfer_ids:
                    # Manage currency.
                    if payment.currency_id == company_currency:
                        # Single-currency.
                        balance = line.amount * sign
                        fee = line.fee
                        transfer_amount = (
                            sum(payment.batch_transfer_ids.mapped("amount")) * sign
                        )
                        currency_id = False
                    else:
                        # Multi-currencies.
                        balance = payment.currency_id._convert(
                            line.amount * sign,
                            company_currency,
                            payment.company_id,
                            payment.payment_date,
                        )
                        fee = payment.currency_id._convert(
                            line.fee,
                            company_currency,
                            payment.company_id,
                            payment.payment_date,
                        )
                        transfer_amount = payment.currency_id._convert(
                            sum(payment.batch_transfer_ids.mapped("amount")) * sign,
                            company_currency,
                            payment.company_id,
                            payment.payment_date,
                        )
                        currency_id = payment.currency_id.id
                    # Transfer Fee line
                    if journal_id == payment.deduct_journal_id.id and line.fee != 0.0:
                        account = payment.deduct_journal_id.default_debit_account_id
                        lines.append(
                            (
                                0,
                                0,
                                {
                                    "name": line.description,
                                    "amount_currency": -line.fee
                                    if currency_id
                                    else 0.0,
                                    "currency_id": currency_id,
                                    "debit": 0.0,
                                    "credit": fee,
                                    "date_maturity": payment.payment_date,
                                    "partner_id": payment.partner_id.id,
                                    "account_id": account.id,
                                    "payment_id": payment.id,
                                },
                            )
                        )
                        lines.append(
                            (
                                0,
                                0,
                                {
                                    "name": line.description,
                                    "amount_currency": line.fee if currency_id else 0.0,
                                    "currency_id": currency_id,
                                    "debit": fee,
                                    "credit": 0.0,
                                    "date_maturity": payment.payment_date,
                                    "partner_id": payment.partner_id.id,
                                    "account_id": payment.writeoff_account_id.id,
                                    "payment_id": payment.id,
                                },
                            )
                        )
                    # Liquidity credit line.
                    lines.append(
                        (
                            0,
                            0,
                            {
                                "name": line_name,
                                "amount_currency": balance > 0.0
                                and -line.amount
                                or line.amount
                                if currency_id
                                else 0.0,
                                "currency_id": currency_id,
                                "debit": balance < 0.0 and -balance or 0.0,
                                "credit": balance > 0.0 and balance or 0.0,
                                "date_maturity": payment.payment_date,
                                "partner_id": payment.partner_id.id,
                                "account_id": account_id,
                                "payment_id": payment.id,
                            },
                        )
                    )

                # Transfer debit line.
                lines.append(
                    (
                        0,
                        0,
                        {
                            "name": payment.name,
                            "amount_currency": sum(
                                payment.batch_transfer_ids.mapped("amount")
                            )
                            * sign
                            if currency_id
                            else 0.0,
                            "currency_id": currency_id,
                            "debit": transfer_amount > 0.0 and transfer_amount or 0.0,
                            "credit": transfer_amount < 0.0 and -transfer_amount or 0.0,
                            "date_maturity": payment.payment_date,
                            "partner_id": payment.partner_id.id,
                            "account_id": payment.company_id.transfer_account_id.id,
                            "payment_id": payment.id,
                        },
                    )
                )
        return res


class AccountTransferLine(models.Model):
    _name = "account.payment.batch.transfer"
    _description = "Payment Batch Transfer"

    payment_id = fields.Many2one(
        comodel_name="account.payment", string="Bank Account Transfer"
    )
    description = fields.Char(help="Label for description fee.")
    amount = fields.Float(required=True)
    fee = fields.Float()
