# Copyright 2018 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2018 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAbstractPayment(models.AbstractModel):
    _name = "account.promissory.note.mixin"
    _description = "Promissory Note Mixin"

    promissory_note = fields.Boolean(string="Promissory Note",)
    date_due = fields.Date(string="Due Date",)

    @api.onchange("promissory_note")
    def _onchange_promissory_note(self):
        if not self.promissory_note:
            self.date_due = False
