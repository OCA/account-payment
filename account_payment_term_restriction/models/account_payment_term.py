# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    applicable_on = fields.Selection(
        selection="_selection_applicable_on",
        default=lambda self: self._get_default_applicable_on(),
    )

    @api.model
    def _selection_applicable_on(self):
        return [
            ("sale", "Sales"),
            ("purchase", "Purchases"),
            ("all", "All"),
        ]

    @api.model
    def _get_default_applicable_on(self):
        return "all"

    @api.model
    def get_sale_applicable_on(self):
        return ["sale", "all"]

    @api.model
    def get_purchase_applicable_on(self):
        return ["purchase", "all"]

    def _skip_check_not_applicable(self, record):
        """
        :return: bool: returns True if the restriction checks can be skipped either if
        the context to skip the checks is passed or the pre-checks are not fulfilled,
        False otherwise.
        """
        if self.env.context.get("skip_payment_term_restriction", False):
            return True
        skip = not bool(
            self
            and len(self) == 1
            and self.applicable_on
            and record
            and isinstance(record, models.BaseModel)
            and ("partner_id" in record._fields or record._name == "res.partner")
        )
        return skip

    def check_not_applicable(self, applicable_on, record):
        """
        :return: bool: returns True if all checks are passed correctly, False if the
        pre-check for the values used in the validation fails.

        Raises a ValidationError if the Payment Term doesn't comply with the checks.
        """
        if self._skip_check_not_applicable(record):
            return False
        if applicable_on and self.applicable_on not in applicable_on:
            sale = "sale" in applicable_on
            msg = "You can only assign Payment Terms of type %s or All." % (
                "Sales" if sale else "Purchases"
            )
            raise ValidationError(_(msg))
        return True
