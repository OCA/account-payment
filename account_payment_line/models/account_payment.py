# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class AccountPayment(models.Model):
    _inherit = "account.payment"

    line_payment_counterpart_ids = fields.One2many(
        "account.payment.counterpart.line",
        "payment_id",
        string="Counterpart Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Use these lines to add matching lines, for example in a credit"
        "card payment, financing interest or commission is added",
    )
    writeoff_account_id = fields.Many2one(
        "account.account",
        string="Write-off Account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
    )

    def _process_post_reconcile(self):
        for rec in self:
            for line in rec.line_payment_counterpart_ids:
                if line.aml_id:
                    to_reconcile = (line.aml_id + line.move_ids).filtered(
                        lambda x: not x.reconciled and x.account_id.reconcile
                    )
                    if to_reconcile:
                        to_reconcile.reconcile()
        return True

    def _get_moves_domain(self):
        domain = [
            ("amount_residual", "!=", 0.0),
            ("state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
            (
                "commercial_partner_id",
                "=",
                self.partner_id.commercial_partner_id.id,
            ),
        ]
        if self.partner_type == "supplier":
            if self.payment_type == "outbound":
                domain.append(("move_type", "in", ("in_invoice", "in_receipt")))
            if self.payment_type == "inbound":
                domain.append(("move_type", "=", "in_refund"))
        elif self.partner_type == "customer":
            if self.payment_type == "outbound":
                domain.append(("move_type", "=", "out_refund"))
            if self.payment_type == "inbound":
                domain.append(("move_type", "in", ("out_invoice", "out_receipt")))
        return domain

    def _filter_amls(self, amls):
        return amls.filtered(
            lambda x: x.partner_id.commercial_partner_id.id
            == self.partner_id.commercial_partner_id.id
            and x.amount_residual != 0
            and x.account_id.internal_type in ("receivable", "payable")
        )

    def _hook_create_new_line(self, invoice, aml, amount_to_apply):
        line_model = self.env["account.payment.counterpart.line"]
        self.ensure_one()
        return line_model.create(
            {
                "payment_id": self.id,
                "name": "/",
                "move_id": invoice.id,
                "aml_id": aml.id,
                "account_id": aml.account_id.id,
                "partner_id": self.partner_id.commercial_partner_id.id,
                "amount": amount_to_apply,
            }
        )

    def action_propose_payment_distribution(self):
        move_model = self.env["account.move"]
        for rec in self:
            if self.is_internal_transfer:
                continue
            domain = self._get_moves_domain()
            pending_invoices = move_model.search(domain, order="invoice_date_due ASC")
            pending_amount = rec.amount
            rec.line_payment_counterpart_ids.unlink()
            for invoice in pending_invoices:
                for aml in self._filter_amls(invoice.line_ids):
                    amount_to_apply = 0
                    amount_residual = rec.company_id.currency_id._convert(
                        aml.amount_residual,
                        rec.currency_id,
                        rec.company_id,
                        date=rec.date,
                    )
                    if pending_amount >= 0:
                        amount_to_apply = min(abs(amount_residual), pending_amount)
                        pending_amount -= abs(amount_residual)
                    rec._hook_create_new_line(invoice, aml, amount_to_apply)

    def action_delete_counterpart_lines(self):
        if self.line_payment_counterpart_ids and self.state == "draft":
            self.line_payment_counterpart_ids = [(5, 0, 0)]

    def _prepare_move_line_default_vals(self, write_off_line_vals=False):
        res = super(AccountPayment, self)._prepare_move_line_default_vals(
            write_off_line_vals
        )
        write_off_amount_currency = (
            write_off_line_vals and write_off_line_vals.get("amount", 0.0) or 0.0
        )
        if self.payment_type == "outbound":
            write_off_amount_currency *= -1
        write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        new_aml_lines = []
        for line in self.line_payment_counterpart_ids.filtered(
            lambda x: not float_is_zero(
                x.amount, precision_digits=self.currency_id.decimal_places
            )
        ):
            line_balance = (
                line.amount if self.payment_type == "outbound" else line.amount * -1
            )
            line_balance_currency = (
                line.amount_currency
                if self.payment_type == "outbound"
                else line.amount_currency * -1
            )
            aml_value = line_balance_currency + write_off_balance
            aml_value_currency = line_balance + write_off_amount_currency
            if line.fully_paid and not float_is_zero(
                line.writeoff_amount, precision_digits=self.currency_id.decimal_places
            ):
                write_off_account = (
                    line.writeoff_account_id.id or self.writeoff_account_id.id
                )
                if not write_off_account:
                    raise ValidationError(
                        _(
                            "Write-off account is not set for payment %s"
                            % self.display_name
                        )
                    )
                # Fully Paid line
                new_aml_lines.append(
                    {
                        "name": line.display_name,
                        "debit": line.aml_amount_residual < 0.0
                        and abs(line.aml_amount_residual)
                        or 0.0,
                        "credit": line.aml_amount_residual > 0.0
                        and abs(line.aml_amount_residual)
                        or 0.0,
                        "amount_currency": abs(line.aml_amount_residual_currency)
                        * (line.aml_amount_residual > 0.0 and -1 or 1),
                        "date_maturity": self.date,
                        "partner_id": line.partner_id.commercial_partner_id.id,
                        "account_id": line.account_id.id,
                        "currency_id": line.payment_id.currency_id.id,
                        "payment_id": self.id,
                        "payment_line_id": line.id,
                        "analytic_account_id": line.analytic_account_id.id,
                        "analytic_tag_ids": line.analytic_tag_ids
                        and [(6, 0, line.analytic_tag_ids.ids)]
                        or [],
                    }
                )
                # write-off line
                new_aml_lines.append(
                    {
                        "name": _("Write-off"),
                        "debit": line.writeoff_amount > 0.0
                        and line.writeoff_amount
                        or 0.0,
                        "credit": line.writeoff_amount < 0.0
                        and -line.writeoff_amount
                        or 0.0,
                        "amount_currency": abs(line.writeoff_amount_currency)
                        * (line.writeoff_amount < 0.0 and -1 or 1),
                        "date_maturity": self.date,
                        "partner_id": line.partner_id.commercial_partner_id.id,
                        "account_id": write_off_account,
                        "currency_id": line.payment_id.currency_id.id,
                        "payment_id": self.id,
                        "payment_line_id": line.id,
                        "analytic_account_id": line.analytic_account_id.id,
                        "analytic_tag_ids": line.analytic_tag_ids
                        and [(6, 0, line.analytic_tag_ids.ids)]
                        or [],
                    }
                )

            else:
                new_aml_lines.append(
                    {
                        "name": line.display_name,
                        "debit": aml_value > 0.0 and aml_value or 0.0,
                        "credit": aml_value < 0.0 and -aml_value or 0.0,
                        "amount_currency": abs(aml_value_currency)
                        * (aml_value < 0.0 and -1 or 1),
                        "date_maturity": self.date,
                        "partner_id": line.partner_id.commercial_partner_id.id,
                        "account_id": line.account_id.id,
                        "currency_id": line.payment_id.currency_id.id,
                        "payment_id": self.id,
                        "payment_line_id": line.id,
                        "analytic_account_id": line.analytic_account_id.id,
                        "analytic_tag_ids": line.analytic_tag_ids
                        and [(6, 0, line.analytic_tag_ids.ids)]
                        or [],
                    }
                )
        if len(res) >= 2 and new_aml_lines:
            res.pop(1)
            res += new_aml_lines
        return res

    def _check_writeoff_lines(self):
        for rec in self:
            writeoff_lines = rec.line_payment_counterpart_ids.filtered(
                lambda x: x.fully_paid
                and not float_is_zero(
                    x.writeoff_amount, precision_digits=rec.currency_id.decimal_places
                )
            )
            if not rec.writeoff_account_id and not all(
                line.writeoff_account_id for line in writeoff_lines
            ):
                raise ValidationError(
                    _(
                        "You should set up write-off account on lines or in header to continue"
                    )
                )

    def action_post(self):
        self._check_writeoff_lines()
        for rec in self.filtered(lambda x: x.line_payment_counterpart_ids):
            if rec.move_id.line_ids:
                rec.move_id.line_ids.unlink()
            rec.move_id.line_ids = [
                (0, 0, line_vals) for line_vals in rec._prepare_move_line_default_vals()
            ]
        res = super(AccountPayment, self).action_post()
        self._process_post_reconcile()
        return res

    def action_draft(self):
        res = super().action_draft()
        for rec in self.filtered(lambda x: x.line_payment_counterpart_ids):
            # CHECK ME: force to recreate lines
            # if document back to draft state,
            # because we can change counterpart lines,
            # but change will not be propagated properly
            rec.move_id.line_ids.unlink()
        return res


class AccountPaymentCounterLine(models.Model):
    _name = "account.payment.counterpart.line"
    _inherit = "account.payment.counterpart.line.abstract"
    _description = "Counterpart line payment"

    payment_id = fields.Many2one(
        "account.payment", string="Payment", required=False, ondelete="cascade"
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        relation="counterpart_line_analytic_tag_rel",
        column1="line_id",
        column2="tag_id",
        string="Analytic Tags",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
    )

    def _get_onchange_fields(self):
        return (
            "aml_id.amount_residual",
            "amount",
            "payment_id.currency_id",
            "payment_id.date",
            "fully_paid",
        )
