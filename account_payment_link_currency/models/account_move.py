# Copyright 2026 volkantasci
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("transaction_ids")
    def _compute_amount_paid(self):
        res = super()._compute_amount_paid()
        for invoice in self:
            done_txs = invoice.transaction_ids.filtered(
                lambda tx: tx.state in ("authorized", "done")
            )
            if any(tx.currency_id != invoice.currency_id for tx in done_txs):
                total = 0.0
                company_curr = invoice.company_currency_id
                for tx in done_txs:
                    if tx.currency_id == invoice.currency_id:
                        total += tx.amount
                    elif (
                        tx.currency_id == company_curr
                        and invoice.amount_total
                        and abs(invoice.amount_total_signed)
                    ):
                        rate = invoice.amount_total / abs(invoice.amount_total_signed)
                        total += invoice.currency_id.round(tx.amount * rate)
                    else:
                        total += tx.currency_id._convert(
                            tx.amount,
                            invoice.currency_id,
                            invoice.company_id,
                            invoice.invoice_date or fields.Date.context_today(invoice),
                        )
                invoice.amount_paid = total
        return res
