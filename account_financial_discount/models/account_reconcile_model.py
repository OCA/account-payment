# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, float_round


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    apply_financial_discounts = fields.Boolean(string="Consider financial discounts")

    financial_discount_label = fields.Char(
        string="Write-off label", default="Financial discount"
    )
    financial_discount_revenue_account_id = fields.Many2one(
        "account.account",
        string="Revenue write-off account",
        related="company_id.financial_discount_revenue_account_id",
        readonly=False,
    )
    financial_discount_expense_account_id = fields.Many2one(
        "account.account",
        string="Expense write-off account",
        related="company_id.financial_discount_expense_account_id",
        readonly=False,
    )
    financial_discount_tolerance = fields.Float(
        help="Tolerance for the application of financial discounts. Use 0.05 to"
        "apply discount up to a difference of 5 cts between statement line"
        "and move lines."
    )

    @api.constrains(
        "rule_type",
        "apply_financial_discounts",
        "match_total_amount",
        # "strict_match_total_amount",
        "financial_discount_label",
        "financial_discount_revenue_account_id",
        "financial_discount_expense_account_id",
        "match_same_currency",
    )
    def _check_apply_financial_discounts(self):
        """Ensure rec model is set up properly to handle financial discounts"""
        for rec in self:
            if rec.rule_type != "invoice_matching" or not rec.apply_financial_discounts:
                continue
            errors = []
            if not rec.match_total_amount or rec.match_total_amount_param != 100.0:
                errors.append(_("Amount Matching must be set to 100%"))
            # if not rec.strict_match_total_amount:
            #     errors.append(_("Strict amount matching must be set"))
            # FIXME: Restrict application of financial discount if currencies
            #  are different while odoo hasn't fixed their mess
            #  cf https://github.com/odoo/odoo/pull/52529#pullrequestreview-427812393
            #  N.B: multicurrency handling is still in the process to avoid
            #  having to rewrite everything once fixed upstream
            if not rec.match_same_currency:
                errors.append(_("Same currency matching must be set"))
            if not rec.financial_discount_label:
                errors.append(_("A financial discount label must be set"))
            if not rec.financial_discount_revenue_account_id:
                errors.append(
                    _(
                        "A financial discount revenue account must be set on "
                        "the company"
                    )
                )
            if not rec.financial_discount_expense_account_id:
                errors.append(
                    _(
                        "A financial discount expense account must be set on "
                        "the company"
                    )
                )
            if errors:
                msg = (
                    _(
                        "Reconciliation model %s is set to consider financial "
                        "discount. However to function properly:\n"
                    )
                    % rec.name
                )
                raise ValidationError(msg + " - " + "\n - ".join(errors))

    def _prepare_reconciliation(self, st_line, aml_ids=None, partner=None):
        if aml_ids is None:
            aml_ids = []
        # TODO Check if there's any better way to pass this than context
        self = self.with_context(_prepare_reconciliation_aml_ids=aml_ids)
        return super()._prepare_reconciliation(
            st_line, aml_ids=aml_ids, partner=partner
        )

    def _get_write_off_move_lines_dict(self, st_line, residual_balance):
        res = super()._get_write_off_move_lines_dict(st_line, residual_balance)
        if (
            self.rule_type != "invoice_matching"
            or res
            or not self.apply_financial_discounts
        ):
            return res
        move_lines = self.env["account.move.line"].browse(
            self.env.context.get("_prepare_reconciliation_aml_ids")
        )
        currency_rounding = fields.first(move_lines).company_id.currency_id.rounding
        if (
            move_lines
            and any(
                move_lines.with_context(discount_date=st_line.date).mapped(
                    "move_id.has_discount_available"
                )
            )
            and float_round(
                abs(
                    sum(move_lines.mapped("amount_discount"))
                    - float_round(
                        residual_balance, precision_rounding=currency_rounding
                    )
                ),
                precision_rounding=currency_rounding,
            )
            <= self.financial_discount_tolerance
        ):

            fin_disc_write_off_vals = self._prepare_financial_discount_write_off_values(
                st_line, move_lines, residual_balance
            )
            res += fin_disc_write_off_vals
        return res

    def _prepare_financial_discount_write_off_values(
        self, st_line, move_lines, residual_balance
    ):
        """Prepare financial discount write-off"""
        res = []
        line_currency = (
            st_line.currency_id
            or st_line.journal_id.currency_id
            or st_line.company_id.currency_id
        )

        if float_is_zero(residual_balance, precision_rounding=line_currency.rounding):
            return res

        write_off_account = (
            self.financial_discount_expense_account_id
            if residual_balance > 0
            else self.financial_discount_revenue_account_id
        )

        fin_disc_write_off_vals = {
            "name": self.financial_discount_label,
            "account_id": write_off_account.id,
            "debit": residual_balance > 0 and residual_balance or 0,
            "credit": residual_balance < 0 and -residual_balance or 0,
            "reconcile_model_id": self.id,
            "balance": residual_balance,
            "currency_id": line_currency.id,
            "journal_id": False,
        }
        res.append(fin_disc_write_off_vals)

        for line in move_lines:
            tax_discount = line.amount_discount_tax
            if not tax_discount:
                continue
            tax_line = line.discount_tax_line_id
            if not tax_line:
                continue
            tax = tax_line.tax_line_id

            tax_write_off_vals = self._get_taxes_move_lines_dict(
                tax.with_context(force_price_include=True), fin_disc_write_off_vals
            )
            fin_disc_write_off_vals["tax_ids"] = [(6, None, tax.ids)]
            res += tax_write_off_vals

        return res

    # flake8: noqa

    # TODO: Check if still needed with strict_match_amount
    def _get_select_communication_flag(self):
        """Consider financial discount to allow reconciliation with the prop"""
        comm_flag = super()._get_select_communication_flag()
        # if self.match_total_amount and self.strict_match_total_amount:
        comm_flag = (
            r"""
            COALESCE(
            """
            + comm_flag.replace("AS communication_flag", "")
            + r"""
            , FALSE)
            AND
            CASE
                WHEN abs(st_line.amount) < abs(aml.balance) - abs(aml.amount_discount) THEN (abs(st_line.amount) - abs(aml.amount_discount)) / abs(aml.balance) * 100
                WHEN abs(st_line.amount) > abs(aml.balance) + abs(aml.amount_discount) THEN (abs(aml.balance) + abs(aml.amount_discount)) / abs(st_line.amount) * 100
                ELSE 100
            END >= {match_total_amount_param}
                """.format(
                match_total_amount_param=self.match_total_amount_param
            )
        )
        return comm_flag

    def _get_invoice_matching_query(self, st_lines_with_partner, excluded_ids):
        """Add fields used for financial discount"""
        query, params = super()._get_invoice_matching_query(
            st_lines_with_partner, excluded_ids
        )
        extra_select = r""",
            account.internal_type AS account_internal_type,
            aml.amount_discount AS discount_amount,
            aml.amount_discount_currency AS discount_amount_currency,
            aml.date_discount AS discount_date,
            move.force_financial_discount AS force_financial_discount
        """
        from_split_query = query.split("FROM")
        base_select = from_split_query[0]
        query_without_select = from_split_query[1:]
        discount_query = " FROM ".join(
            [base_select + extra_select] + query_without_select
        )
        return discount_query, params
