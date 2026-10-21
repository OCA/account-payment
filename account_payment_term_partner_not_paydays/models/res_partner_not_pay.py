# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartnerNotPay(models.Model):
    _name = "res.partner.not.pay"
    _description = "Days of non-payment to the partner"

    partner_id = fields.Many2one("res.partner")
    date_start = fields.Date(string="Start", required=True)
    date_end = fields.Date(string="End", required=True)
    type = fields.Selection(
        [
            ("entry", "Journal Entry"),
            ("out_invoice", "Customer Invoice"),
            ("out_refund", "Customer Credit Note"),
            ("in_invoice", "Vendor Bill"),
            ("in_refund", "Vendor Credit Note"),
            ("out_receipt", "Sales Receipt"),
            ("in_receipt", "Purchase Receipt"),
        ],
        default="out_invoice",
        required=True,
    )

    @api.constrains("date_start", "date_end")
    def _check_date_start_end(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(_("Date start must be less than date end."))
            else:
                overlap = self.search_read(
                    [
                        ("date_start", "<=", record.date_end),
                        ("date_end", ">=", record.date_start),
                        ("id", "!=", record.id),
                        ("partner_id", "=", record.partner_id.id),
                    ],
                    ["date_start", "date_end"],
                    limit=1,
                )
                if overlap:
                    raise ValidationError(
                        _(
                            "The start %(start)s and %(end)s values overlap with:"
                            "\nOverlap: Start: %(start_overlap)s End: %(end_overlap)s"
                        )
                        % {
                            "start": record.date_start,
                            "end": record.date_end,
                            "start_overlap": overlap[0]["date_start"].strftime(
                                "%d/%m/%Y"
                            ),
                            "end_overlap": overlap[0]["date_end"].strftime("%d/%m/%Y"),
                        }
                    )
