# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestBalance(SavepointCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        cls.partner = cls.env.ref("base.res_partner_address_30")
        cls.customer_wallet_account = cls.env.ref(
            "account_customer_wallet.account_account_customer_wallet_demo"
        )
        cls.customer_wallet_journal = cls.env.ref(
            "account_customer_wallet.account_journal_customer_wallet_demo"
        )
        cls.cash_account = cls.env["account.account"].search(
            [("user_type_id.type", "=", "liquidity")], limit=1
        )

        cls.company_id = cls.env.user.company_id
        cls.company_id.customer_wallet_account_id = cls.customer_wallet_account
        cls.company_id.customer_wallet = True

    def _create_move(self, debit=0, credit=0, partner=None):
        if partner is None:
            partner = self.partner

        self.env["account.move"].create(
            {
                "journal_id": self.customer_wallet_journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "debit": debit,
                            "credit": credit,
                            "partner_id": partner.id,
                            "account_id": self.customer_wallet_account.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "debit": credit,
                            "credit": debit,
                            "partner_id": partner.id,
                            "account_id": self.cash_account.id,
                        },
                    ),
                ],
            }
        )
