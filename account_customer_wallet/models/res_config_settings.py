# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools.translate import _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_customer_wallet = fields.Boolean(
        string="Account Customer Wallet",
        config_parameter="account_customer_wallet.account_customer_wallet",
        help="Let customers pay from a wallet account",
    )
    customer_wallet_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Customer Wallet Journal",
    )

    @api.onchange("account_customer_wallet", "customer_wallet_journal_id")
    def _onchange_customer_wallet(self):
        """Do not allow *account_customer_wallet* to be enabled without defining
        *customer_wallet_journal_id*. There is probably a better way to do this.
        """
        res = {}
        if self.account_customer_wallet and not self.customer_wallet_journal_id:
            self.account_customer_wallet = False
            res["warning"] = {
                "title": _("Error!"),
                "message": _(
                    "You cannot enable this setting without defining a customer"
                    " wallet journal."
                ),
            }
        return res
