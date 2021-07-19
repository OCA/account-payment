# Copyright 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    early_payment_discount = fields.Boolean(
        string="Early Payment Discount",
    )

    epd_nb_days = fields.Integer(string="Number of day(s)")
    epd_discount = fields.Float(string="Discount")
    epd_tolerance = fields.Float(string="Tolerance")

    company_currency = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_company_currency',
        required=True
    )

    _sql_constraints = [(
        'early_payment_discount',

        'CHECK '
        '(NOT early_payment_discount OR'
        ' (NULLIF(epd_nb_days, 0) IS NOT NULL AND'
        '  NULLIF(epd_discount, 0) IS NOT NULL)'
        ')',

        _("'Number of day(s)' and 'Discount' fields "
          "must be filled if 'Early Payment Discount' is checked")
    )]

    def _compute_company_currency(self):
        self.company_currency = self.env.user.company_id.currency_id

    @api.onchange('early_payment_discount')
    def _onchange_early_payment_discount(self):
        if not self.early_payment_discount:
            self.epd_nb_days = False
            self.epd_discount = False
            self.epd_tolerance = False
