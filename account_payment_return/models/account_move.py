# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from operator import itemgetter

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    returned_payment = fields.Boolean(
        string="Payment returned",
        help="Invoice has been included on a payment that has been returned later.",
    )

    def check_payment_return(self):
        returned_invoices = (
            self.env["account.partial.reconcile"]
            .search([("origin_returned_move_ids.move_id", "in", self.ids)])
            .mapped("origin_returned_move_ids.move_id")
        )
        returned_invoices.filtered(lambda x: not x.returned_payment).write(
            {"returned_payment": True}
        )
        (self - returned_invoices).filtered("returned_payment").write(
            {"returned_payment": False}
        )

    def _get_reconciled_info_JSON_values(self):
        values = super()._get_reconciled_info_JSON_values()
        if not self.returned_payment:
            return values
        returned_reconciles = self.env["account.partial.reconcile"].search(
            [("origin_returned_move_ids.move_id", "=", self.id)]
        )
        for returned_reconcile in returned_reconciles:
            payment = returned_reconcile.credit_move_id
            payment_ret = returned_reconcile.debit_move_id
            values.append(
                {
                    "name": payment.name,
                    "journal_name": payment.journal_id.name,
                    "amount": returned_reconcile.amount,
                    "currency": self.currency_id.symbol,
                    "digits": [69, self.currency_id.decimal_places],
                    "position": self.currency_id.position,
                    "date": payment.date,
                    "payment_id": payment.id,
                    "move_id": payment.move_id.id,
                    "ref": payment.move_id.name,
                }
            )
            values.append(
                {
                    "name": payment_ret.name,
                    "journal_name": payment_ret.journal_id.name,
                    "amount": -returned_reconcile.amount,
                    "currency": self.currency_id.symbol,
                    "digits": [69, self.currency_id.decimal_places],
                    "position": self.currency_id.position,
                    "date": payment_ret.date,
                    "payment_id": payment_ret.id,
                    "move_id": payment_ret.move_id.id,
                    "ref": "{} ({})".format(
                        payment_ret.move_id.name, payment_ret.move_id.ref
                    ),
                    "returned": True,
                }
            )
        return sorted(values, key=itemgetter("date"), reverse=True)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    partial_reconcile_returned_ids = fields.Many2many(
        comodel_name="account.partial.reconcile",
        relation="account_partial_reconcile_account_move_line_rel",
        column1="move_line_id",
        column2="partial_reconcile_id",
    )


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    origin_returned_move_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="account_partial_reconcile_account_move_line_rel",
        column1="partial_reconcile_id",
        column2="move_line_id",
    )
