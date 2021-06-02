# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentTerminal(models.Model):

    _name = "account.payment.terminal"
    _description = "Account Payment Terminal"

    name = fields.Char(required=True)
    proxy_ip = fields.Char(
        string="IP Address",
        size=45,
        help="The hostname or ip address of the hardware proxy",
        required=True,
    )
    oca_payment_terminal_id = fields.Char(
        string="Terminal identifier",
        help=(
            "The identifier of the terminal as known by the hardware proxy. "
            "Leave empty if the proxy has only one terminal connected."
        ),
    )
