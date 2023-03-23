# Copyright 2016 Tecnativa .- Carlos Dauden
# Copyright 2016 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentReturnLine(models.Model):
    _inherit = "payment.return.line"

    # Ensure transactions can be imported only once (if the import format
    # provides unique transaction ids)
    unique_import_id = fields.Char(string="Import ID", readonly=True, copy=False)
    raw_import_data = fields.Char(
        help="XML RAW data stored for debugging/check purposes"
    )

    _sql_constraints = [
        (
            "unique_import_id",
            "unique (unique_import_id)",
            "A payment return transaction can be imported only once!",
        )
    ]
