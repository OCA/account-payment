# Copyright 2016 Tecnativa Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, fields, models
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

    def prepare_values_returned_widget(self, line_id, amount, is_return=False):
        try:
            payment_method_name = line_id.payment_method_line_id.name
        except AttributeError:
            payment_method_name = False
        ref = line_id.memo if hasattr(line_id, "memo") else line_id.ref
        return {
            "name": line_id.name,
            "journal_name": line_id.journal_id.name,
            "amount": amount,
            "date": line_id.date,
            "partial_id": line_id.id,
            "currency_id": line_id.currency_id,
            "currency": line_id.currency_id.symbol,
            "position": line_id.currency_id.position,
            "move_id": line_id.move_id.id,
            "amount_company_currency": formatLang(
                self.env,
                abs(amount),
                currency_obj=line_id.currency_id,
            ),
            "payment_method_name": payment_method_name,
            "ref": f"{line_id.move_id.name} ({ref})",
            "returned": is_return,
            "is_exchange": False,
        }

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
                    "title": _("Returned on"),
                }
                domain = [("origin_returned_move_ids.move_id", "=", move.id)]
                for reconciled_aml in move._get_reconciled_amls():
                    vals_rec_payment = self.prepare_values_returned_widget(
                        reconciled_aml, -reconciled_aml.balance
                    )
                    values_returned.append(vals_rec_payment)
                move_reconciles = self.env["account.partial.reconcile"].search(domain)
                for move_reconcile in move_reconciles:
                    payment_ret = move_reconcile.debit_move_id
                    payment = move_reconcile.credit_move_id
                    vals_payment = self.prepare_values_returned_widget(
                        payment, move_reconcile.amount
                    )
                    values_returned.append(vals_payment)
                    vals_reconcile = self.prepare_values_returned_widget(
                        payment_ret, -move_reconcile.amount, True
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
