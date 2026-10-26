# Copyright 2026 volkantasci
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models

from odoo.addons.payment import utils as payment_utils


class PaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    previous_currency_id = fields.Many2one(
        comodel_name="res.currency",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get("currency_id") and not res.get("previous_currency_id"):
            res["previous_currency_id"] = res["currency_id"]
        return res

    @api.model_create_multi
    def create(self, vals_list):
        wizards = super().create(vals_list)
        for wizard, vals in zip(wizards, vals_list, strict=True):
            old_currency = wizard.previous_currency_id
            new_currency = wizard.currency_id
            if old_currency and new_currency and old_currency != new_currency:
                if "amount_max" not in vals:
                    wizard.amount_max = wizard._convert_document_amount(
                        wizard.amount_max, old_currency, new_currency
                    )
                if "amount" not in vals:
                    wizard.amount = wizard._convert_document_amount(
                        wizard.amount, old_currency, new_currency
                    )
                wizard._convert_open_installments(old_currency, new_currency)
                wizard.previous_currency_id = new_currency
        return wizards

    @api.onchange("currency_id")
    def _onchange_currency_id(self):
        for wizard in self:
            old_currency = wizard.previous_currency_id
            new_currency = wizard.currency_id
            if old_currency and new_currency and old_currency != new_currency:
                wizard.amount_max = wizard._convert_document_amount(
                    wizard.amount_max, old_currency, new_currency
                )
                wizard.amount = wizard._convert_document_amount(
                    wizard.amount, old_currency, new_currency
                )
                wizard._convert_open_installments(old_currency, new_currency)
                wizard.previous_currency_id = new_currency
            elif new_currency and not old_currency:
                wizard.previous_currency_id = new_currency

    def _convert_open_installments(self, from_currency, to_currency):
        self.ensure_one()
        if not self.open_installments:
            return
        self.open_installments = [
            {
                **installment,
                "amount": self._convert_document_amount(
                    installment["amount"], from_currency, to_currency
                ),
            }
            for installment in self.open_installments
        ]

    def _convert_document_amount(self, amount, from_currency, to_currency):
        self.ensure_one()
        if (
            not amount
            or not from_currency
            or not to_currency
            or from_currency == to_currency
        ):
            return amount

        related_document = (
            self.env[self.res_model].browse(self.res_id)
            if self.res_model and self.res_id
            else self.env["account.move"]
        )
        if self.res_model == "account.move" and related_document.exists():
            doc_curr = related_document.currency_id
            comp_curr = related_document.company_currency_id
            if (
                {from_currency, to_currency} == {doc_curr, comp_curr}
                and related_document.amount_residual
                and related_document.amount_residual_signed
            ):
                from_total = (
                    abs(related_document.amount_residual)
                    if from_currency == doc_curr
                    else abs(related_document.amount_residual_signed)
                )
                to_total = (
                    abs(related_document.amount_residual)
                    if to_currency == doc_curr
                    else abs(related_document.amount_residual_signed)
                )
                if from_currency.is_zero(amount - from_total):
                    return to_total
                if from_total:
                    return to_currency.round(amount * (to_total / from_total))
            date = (
                related_document.invoice_date
                or related_document.date
                or fields.Date.context_today(self)
            )
            company = related_document.company_id or self.env.company
            return from_currency._convert(amount, to_currency, company, date)

        date = fields.Date.context_today(self)
        company = self.company_id or self.env.company
        return from_currency._convert(amount, to_currency, company, date)

    def _is_custom_currency(self, related_document):
        self.ensure_one()
        doc_currency = (
            related_document.currency_id if "currency_id" in related_document else False
        )
        return bool(
            self.currency_id and doc_currency and self.currency_id != doc_currency
        )

    def _prepare_url(self, base_url, related_document):
        res = super()._prepare_url(base_url, related_document)
        if self.res_model == "account.move" and self._is_custom_currency(
            related_document
        ):
            return f"{base_url}/payment/pay"
        return res

    def _prepare_query_params(self, related_document):
        res = super()._prepare_query_params(related_document)
        if self.res_model == "account.move" and self._is_custom_currency(
            related_document
        ):
            reference = related_document.payment_reference or related_document.name
            return {
                "reference": reference,
                "amount": self.amount,
                "currency_id": self.currency_id.id,
                "partner_id": self.partner_id.id,
                "company_id": self.company_id.id,
                "access_token": self._prepare_access_token(),
            }
        return res

    def _prepare_access_token(self):
        res = super()._prepare_access_token()
        if self.res_model == "account.move" and self.res_id:
            related_document = self.env[self.res_model].browse(self.res_id)
            if self._is_custom_currency(related_document):
                return payment_utils.generate_access_token(
                    self.partner_id.id,
                    self.amount,
                    self.currency_id.id,
                    env=self.env,
                )
        return res

    def _prepare_anchor(self):
        res = super()._prepare_anchor()
        if self.res_model == "account.move" and self.res_id:
            related_document = self.env[self.res_model].browse(self.res_id)
            if self._is_custom_currency(related_document):
                return ""
        return res
