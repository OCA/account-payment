from odoo import api, models
from odoo.tools.misc import format_date, formatLang


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _prepare_move_lines(
        self, move_lines, target_currency=False, target_date=False, recs_count=0
    ):
        values = super()._prepare_move_lines(
            move_lines, target_currency, target_date, recs_count
        )

        for line in values:
            move_line = self.env["account.move.line"].browse(line["id"])
            move = move_line.move_id
            company_currency = move_line.account_id.company_id.currency_id
            line_currency = (
                (move_line.currency_id and move_line.amount_currency)
                and move_line.currency_id
                or company_currency
            )

            if move and move.discount_due_date and move.has_discount:
                if target_currency == company_currency:
                    discount_amount = move_line.discount_amount
                else:
                    if line_currency == target_currency:
                        discount_amount = move_line.discount_amount
                    else:
                        company = move_line.account_id.company_id
                        date = target_date or move_line.date
                        discount_amount = company_currency._convert(
                            move_line.discount_amount, target_currency, company, date
                        )

                line["has_discount"] = True
                line["discount_amount"] = formatLang(
                    self.env, discount_amount, currency_obj=target_currency
                )
                line["discount_due_date"] = format_date(
                    self.env, move_line.discount_due_date
                )

        return values
