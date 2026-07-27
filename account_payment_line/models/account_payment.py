# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    line_payment_counterpart_ids = fields.One2many(
        "account.payment.counterpart.line",
        "payment_id",
        string="Counterpart Lines",
        help="Use these lines to add matching lines, for example in a credit"
        "card payment, financing interest or commission is added",
    )
    writeoff_account_id = fields.Many2one(
        "account.account",
        string="Write-off Account",
        domain="[('deprecated', '=', False), ('company_ids', '=', company_id)]",
    )
    restrict_counterpart_partner = fields.Boolean(
        related="company_id.payment_line_restrict_counterpart_partner",
    )

    def _process_post_reconcile(self):
        for rec in self.filtered("line_payment_counterpart_ids"):
            for line in rec.line_payment_counterpart_ids.filtered("aml_id"):
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
        move_type_map = {
            ("supplier", "outbound"): [
                ("move_type", "in", ("in_invoice", "in_receipt"))
            ],
            ("supplier", "inbound"): [("move_type", "=", "in_refund")],
            ("customer", "outbound"): [("move_type", "=", "out_refund")],
            ("customer", "inbound"): [
                ("move_type", "in", ("out_invoice", "out_receipt"))
            ],
        }
        domain.extend(move_type_map.get((self.partner_type, self.payment_type), []))
        return domain

    def _filter_amls(self, amls):
        return amls.filtered(
            lambda x: x.partner_id.commercial_partner_id.id
            == self.partner_id.commercial_partner_id.id
            and x.amount_residual != 0
            and x.account_id.account_type in ("asset_receivable", "liability_payable")
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
        for rec in self:
            domain = rec._get_moves_domain()
            pending_invoices = rec.env["account.move"].search(
                domain, order="invoice_date_due ASC"
            )
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
                    if rec.payment_type == "outbound":
                        amount_to_apply *= -1
                    rec._hook_create_new_line(invoice, aml, amount_to_apply)

    def action_delete_counterpart_lines(self):
        if self.line_payment_counterpart_ids and self.state == "draft":
            self.line_payment_counterpart_ids = [Command.clear()]

    def _prepare_move_line_default_vals(
        self, write_off_line_vals=None, force_balance=None
    ):
        new_write_off_line_vals = self._prepare_move_line_counterpart_vals(
            write_off_line_vals
        )
        if write_off_line_vals:
            new_write_off_line_vals += write_off_line_vals
        vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=new_write_off_line_vals, force_balance=force_balance
        )
        # filter line with both debit and credit equal 0
        filter_vals_list = [vals for vals in vals_list if vals["balance"] != 0.0]
        return filter_vals_list if filter_vals_list else vals_list

    def _prepare_move_line_counterpart_vals(self, write_off_line_vals=None):
        """return list of dictionary
        * amount:       The amount to be added to the counterpart amount.
        * name:         The label to set on the line.
        * account_id:   The account on which create the counterpart line.
        """
        self.ensure_one()
        write_off_line_vals_list = write_off_line_vals or []
        write_off_amount_currency = sum(
            x["amount_currency"] for x in write_off_line_vals_list
        )
        write_off_balance = sum(x["balance"] for x in write_off_line_vals_list)
        is_outbound = self.payment_type == "outbound"
        if is_outbound:
            write_off_amount_currency *= -1
        new_aml_lines = []
        currency_id = self.currency_id
        company_id = self.company_id
        payment_date = self.date
        for line in self.line_payment_counterpart_ids.filtered(
            lambda x: not currency_id.is_zero(x.amount)
        ):
            line_balance = line.amount if is_outbound else line.amount * -1
            line_balance_currency = (
                line.amount_currency if is_outbound else line.amount_currency * -1
            )
            aml_value = line_balance_currency + write_off_balance
            aml_value_currency = line_balance + write_off_amount_currency
            if line.fully_paid and not currency_id.is_zero(line.writeoff_amount):
                write_off_account = (
                    line.writeoff_account_id.id or self.writeoff_account_id.id
                )
                if not write_off_account:
                    raise ValidationError(
                        self.env._(
                            "Write-off account is not set for payment %(name)s",
                            name=self.display_name,
                        )
                    )
                # Fully Paid line
                amount_currency_fully_paid = abs(line.aml_amount_residual_currency) * (
                    line.aml_amount_residual > 0.0 and -1 or 1
                )
                new_aml_lines.append(
                    {
                        "name": line.display_name,
                        "debit": line.aml_amount_residual < 0.0
                        and abs(line.aml_amount_residual)
                        or 0.0,
                        "credit": line.aml_amount_residual > 0.0
                        and abs(line.aml_amount_residual)
                        or 0.0,
                        "amount_currency": amount_currency_fully_paid,
                        "balance": currency_id._convert(
                            amount_currency_fully_paid,
                            company_id.currency_id,
                            company_id,
                            payment_date,
                        ),
                        "date_maturity": payment_date,
                        "partner_id": line.partner_id.commercial_partner_id.id,
                        "account_id": line.account_id.id,
                        "currency_id": line.payment_id.currency_id.id,
                        "payment_id": self.id,
                        "payment_line_id": line.id,
                    }
                )
                # write-off line
                amount_currency_write_off = abs(line.writeoff_amount_currency) * (
                    line.writeoff_amount < 0.0 and -1 or 1
                )
                new_aml_lines.append(
                    {
                        "name": self.env._("Write-off"),
                        "debit": line.writeoff_amount > 0.0
                        and line.writeoff_amount
                        or 0.0,
                        "credit": line.writeoff_amount < 0.0
                        and -line.writeoff_amount
                        or 0.0,
                        "amount_currency": amount_currency_write_off,
                        "balance": currency_id._convert(
                            amount_currency_write_off,
                            company_id.currency_id,
                            company_id,
                            payment_date,
                        ),
                        "date_maturity": payment_date,
                        "partner_id": line.partner_id.commercial_partner_id.id,
                        "account_id": write_off_account,
                        "currency_id": line.payment_id.currency_id.id,
                        "payment_id": self.id,
                        "payment_line_id": line.id,
                    }
                )
            else:
                aml_value *= is_outbound and -1 or 1
                amount_currency = abs(aml_value_currency) * (
                    aml_value < 0.0 and -1 or 1
                )
                new_aml_lines.append(
                    {
                        "name": line.display_name,
                        "debit": aml_value > 0.0 and aml_value or 0.0,
                        "credit": aml_value < 0.0 and -aml_value or 0.0,
                        "amount_currency": amount_currency,
                        "balance": currency_id._convert(
                            amount_currency,
                            company_id.currency_id,
                            company_id,
                            payment_date,
                        ),
                        "date_maturity": payment_date,
                        "partner_id": line.partner_id.commercial_partner_id.id,
                        "account_id": line.account_id.id,
                        "currency_id": line.payment_id.currency_id.id,
                        "payment_id": self.id,
                        "payment_line_id": line.id,
                    }
                )
        return new_aml_lines

    def _check_writeoff_lines(self):
        for rec in self:
            writeoff_lines = rec.line_payment_counterpart_ids.filtered(
                lambda x, currency=rec.currency_id: x.fully_paid
                and not currency.is_zero(x.writeoff_amount)
            )
            if not rec.writeoff_account_id and not all(
                line.writeoff_account_id for line in writeoff_lines
            ):
                raise ValidationError(
                    self.env._(
                        "You should set up write-off account on lines "
                        "or in header to continue"
                    )
                )

    def action_post(self):
        self._check_writeoff_lines()
        for rec in self.filtered("line_payment_counterpart_ids"):
            if rec.move_id.line_ids:
                rec.move_id.line_ids.unlink()
            rec.move_id.line_ids = [
                (0, 0, line_vals) for line_vals in rec._prepare_move_line_default_vals()
            ]
        res = super().action_post()
        self._process_post_reconcile()
        return res

    def action_draft(self):
        res = super().action_draft()
        for rec in self.filtered("line_payment_counterpart_ids"):
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
        "account.payment", string="Payment", ondelete="cascade"
    )
    counterpart_partner_domain = fields.Binary(
        compute="_compute_counterpart_partner_domain",
        help="Technical field holding the domain applied to the partner of the "
        "counterpart line.",
    )

    def _get_onchange_fields(self):
        res = super()._get_onchange_fields()
        return res + ("payment_id.currency_id", "payment_id.date")

    @api.depends("payment_id.partner_id", "payment_id.restrict_counterpart_partner")
    def _compute_counterpart_partner_domain(self):
        for rec in self:
            payment = rec.payment_id
            if not payment.restrict_counterpart_partner:
                rec.counterpart_partner_domain = []
            elif payment.partner_id:
                commercial_partner = payment.partner_id.commercial_partner_id
                rec.counterpart_partner_domain = [
                    ("commercial_partner_id", "=", commercial_partner.id)
                ]
            else:
                # Restriction is on but no partner is set yet: forbid selection
                # instead of offering every partner.
                rec.counterpart_partner_domain = [("id", "=", False)]

    @api.constrains("partner_id", "move_id", "aml_id", "payment_id")
    def _check_counterpart_partner(self):
        for rec in self:
            payment = rec.payment_id
            if not payment or not payment.restrict_counterpart_partner:
                continue
            payment_partner = payment.partner_id.commercial_partner_id
            if not payment_partner:
                continue
            line_partners = (
                rec.partner_id.commercial_partner_id
                | rec.move_id.commercial_partner_id
                | rec.aml_id.partner_id.commercial_partner_id
            )
            if line_partners and line_partners != payment_partner:
                raise ValidationError(
                    self.env._(
                        "You can only apply counterpart lines of %(partner)s, "
                        "the partner set on the payment.",
                        partner=payment_partner.display_name,
                    )
                )
