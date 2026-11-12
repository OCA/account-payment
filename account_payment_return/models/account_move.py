# Copyright 2016 Tecnativa Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.tools import formatLang


class AccountMove(models.Model):
    _inherit = "account.move"

    returned_payment = fields.Boolean(
        string="Payment returned",
        help="Invoice has been included on a payment that has been returned later.",
        copy=False,
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

    def prepare_values_returned_widget(self, line, partial_info, is_return=False):
        move = line.move_id
        payment = line.payment_id
        foreign_currency = (
            line.currency_id
            if line.amount_currency and line.currency_id != line.company_id.currency_id
            else False
        )
        reconciliation_ref = f"{move.name} ({move.ref})" if move.ref else move.name
        return {
            "name": line.name,
            "journal_name": line.journal_id.name,
            "company_name": line.journal_id.company_id.name
            if line.journal_id.company_id != move.company_id
            else False,
            "amount": partial_info["amount"],
            "currency_id": partial_info["currency"].id,
            "date": fields.Date.to_string(line.date),
            "partial_id": partial_info["partial_id"],
            "account_payment_id": payment.id,
            "payment_method_name": payment.payment_method_line_id.name,
            "move_id": move.id,
            "is_refund": move.move_type in ["in_refund", "out_refund"],
            "ref": reconciliation_ref,
            "is_exchange": False,
            "amount_company_currency": formatLang(
                self.env,
                abs(partial_info["company_amount"]),
                currency_obj=line.company_id.currency_id,
            ),
            "amount_foreign_currency": formatLang(
                self.env,
                abs(partial_info["foreign_amount"]),
                currency_obj=foreign_currency,
            )
            if foreign_currency
            else None,
            "returned": is_return,
        }

    @api.depends("move_type", "line_ids.amount_residual", "returned_payment")
    def _compute_payments_widget_reconciled_info(self):
        moves_to_compute = self.env["account.move"]
        for move in self:
            if not move.returned_payment:
                moves_to_compute |= move
            else:
                values_returned = []
                payments_widget_vals = {
                    "outstanding": False,
                    "content": values_returned,
                    "move_id": move.id,
                    "title": self.env._("Returned on"),
                    "exchange_info": {
                        "line_ids": [],
                        "exchange_amount": 0.0,
                        "label": "",
                        "exchange_amount_formatted": formatLang(
                            self.env, 0.0, currency_obj=move.company_currency_id
                        ),
                    },
                }
                domain = [("origin_returned_move_ids.move_id", "=", move.id)]
                for partial_info in move._get_all_reconciled_invoice_partials():
                    vals_rec_payment = move._prepare_payments_widget_reconciled_info(
                        partial_info
                    )
                    vals_rec_payment["date"] = fields.Date.to_string(
                        vals_rec_payment["date"]
                    )
                    values_returned.append(vals_rec_payment)
                move_reconciles = self.env["account.partial.reconcile"].search(domain)
                for move_reconcile in move_reconciles:
                    payment_ret = move_reconcile.debit_move_id
                    payment = move_reconcile.credit_move_id
                    amount = move_reconcile.amount
                    if payment.currency_id == move.currency_id:
                        amount = move_reconcile.credit_amount_currency
                    elif payment.balance:
                        invoice_line = (
                            move_reconcile.origin_returned_move_ids.filtered_domain(
                                [("move_id", "=", move.id)]
                            )[:1]
                        )
                        amount *= abs(invoice_line.amount_currency / payment.balance)
                    partial_info = {
                        "partial_id": move_reconcile.id,
                        "currency": move.currency_id,
                        "amount": amount,
                        "company_amount": move_reconcile.amount,
                        "foreign_amount": move_reconcile.credit_amount_currency,
                    }
                    vals_payment = move.prepare_values_returned_widget(
                        payment, partial_info
                    )
                    values_returned.append(vals_payment)
                    vals_reconcile = move.prepare_values_returned_widget(
                        payment_ret,
                        dict(
                            partial_info,
                            amount=-amount,
                            foreign_amount=move_reconcile.debit_amount_currency,
                        ),
                        True,
                    )
                    values_returned.append(vals_reconcile)
                if payments_widget_vals["content"]:
                    payments_widget_vals["content"] = sorted(
                        payments_widget_vals["content"],
                        key=lambda x: (x["date"], x["partial_id"]),
                    )
                    move.invoice_payments_widget = payments_widget_vals
                else:
                    move.invoice_payments_widget = False
        if moves_to_compute:
            return super(
                AccountMove, moves_to_compute
            )._compute_payments_widget_reconciled_info()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    partial_reconcile_returned_ids = fields.Many2many(
        comodel_name="account.partial.reconcile",
        relation="account_partial_reconcile_account_move_line_rel",
        column1="move_line_id",
        column2="partial_reconcile_id",
        copy=False,
    )


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    origin_returned_move_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="account_partial_reconcile_account_move_line_rel",
        column1="partial_reconcile_id",
        column2="move_line_id",
        copy=False,
    )
