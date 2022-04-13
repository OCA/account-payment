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

        cls.env["ir.config_parameter"].set_param(
            "account_customer_wallet.customer_wallet_account_id",
            cls.customer_wallet_account.id,
        )
        cls.env["ir.config_parameter"].set_param(
            "account_customer_wallet.customer_wallet", True
        )

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

    def test_balance_zero(self):
        """When doing nothing, a partner's balance is zero."""
        self.assertEqual(self.partner.customer_wallet_balance, 0)

    def test_one_credit(self):
        """If there's one credit line on the account, the customer wallet
        balance goes UP.

        In effect, this means that the customer recharged their wallet by giving
        the company some money.
        """
        self._create_move(credit=100)

        self.assertEqual(self.partner.customer_wallet_balance, 100)

    def test_one_debit(self):
        """If there's one debit line on the account, the customer wallet
        balance goes DOWN.

        In effect, this means that the customer paid using their wallet.
        """
        self._create_move(debit=100)

        self.assertEqual(self.partner.customer_wallet_balance, -100)

    def test_different_partner(self):
        """Move lines for other partners do not affect the balances of all
        clients.
        """
        other_partner = self.env.ref("base.res_partner_address_31")
        self._create_move(debit=100, partner=other_partner)

        self.assertEqual(self.partner.customer_wallet_balance, 0)
        self.assertEqual(other_partner.customer_wallet_balance, -100)

    def test_debit_and_credit(self):
        """Debit and credit lines cancel each other out."""
        self._create_move(credit=100)
        self._create_move(debit=50)

        self.assertEqual(self.partner.customer_wallet_balance, 50)
