# Copyright (C) 2017-2021 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class CashInvoiceOut(models.TransientModel):
    _name = "cash.invoice.out"
    _inherit = "cash.box.out"
    _description = "Cash invoice out"

    def _default_value(self, default_function):
        active_model = self.env.context.get("active_model", False)
        if active_model:
            active_ids = self.env.context.get("active_ids", False)
            return default_function(active_model, active_ids)
        return None

    def _default_company(self):
        return self._default_value(self.default_company)

    def _default_currency(self):
        return self._default_value(self.default_currency)

    def _default_journals(self):
        return self._default_value(self.default_journals)

    def _default_journal(self):
        journals = self._default_journals()
        if journals and len(journals) > 0:
            return fields.first(journals).ensure_one()

    def _default_journal_count(self):
        return len(self._default_journals())

    invoice_id = fields.Many2one(
        comodel_name="account.move", string="Invoice", required=True,
    )
    name = fields.Char(related="invoice_id.name",)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self._default_company(),
        required=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self._default_currency(),
        required=True,
        readonly=True,
    )
    journal_ids = fields.Many2many(
        comodel_name="account.journal",
        default=lambda self: self._default_journals(),
        required=True,
        readonly=True,
        string="Journals",
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        required=True,
        default=lambda self: self._default_journal(),
        string="Journal",
    )
    journal_count = fields.Integer(
        default=lambda self: self._default_journal_count(), readonly=True
    )

    def default_company(self, active_model, active_ids):
        return fields.first(self.env[active_model].browse(active_ids)).company_id

    def default_currency(self, active_model, active_ids):
        return self.default_company(active_model, active_ids).currency_id

    def default_journals(self, active_model, active_ids):
        return fields.first(self.env[active_model].browse(active_ids)).journal_id

    @api.onchange("journal_ids")
    def compute_journal_count(self):
        self.journal_count = len(self.journal_ids)

    @api.onchange("journal_id")
    def _onchange_journal(self):
        self.currency_id = (
            self.journal_id.currency_id or self.journal_id.company_id.currency_id
        )

    @api.onchange("invoice_id")
    def _onchange_invoice(self):
        if self.invoice_id:
            self.amount = self.invoice_id.amount_residual_signed

    def _calculate_values_for_statement_line(self, record):
        res = super()._calculate_values_for_statement_line(record)
        res.update(
            {
                "invoice_id": self.invoice_id.id,
                "ref": self.invoice_id.name,
                "partner_id": self.invoice_id.partner_id.id,
            }
        )
        return res
