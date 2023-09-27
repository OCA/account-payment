#  Copyright 2023 Simone Rubino - TAKOBI
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    keep_previous_amount = fields.Boolean()

    @api.depends()
    def _compute_amount(self):
        wizard_to_previous_values = {
            wizard: {
                "amount": wizard.amount,
            }
            for wizard in self
            if wizard.keep_previous_amount
        }

        result = super()._compute_amount()

        for wizard, previous_values in wizard_to_previous_values.items():
            previous_amount = previous_values["amount"]
            currency = wizard.currency_id
            if not currency.is_zero(previous_amount):
                # Restore the previous amount if it is changed
                if currency.compare_amounts(wizard.amount, previous_amount) != 0:
                    wizard.amount = previous_amount
        return result
