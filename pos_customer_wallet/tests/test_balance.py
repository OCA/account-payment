# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from .common import TestPosBalance as TestBalance


class TestPosBalance(TestBalance):
    def test_with_statement(self):
        """Bank statements now also affect balance."""
        self._create_move(credit=100)
        self._create_statement(amount=40)

        self.assertEqual(self.partner.customer_wallet_balance, 60)

    def test_statement_different_partner(self):
        """Statements for other partners do not affect the balances of all
        clients.
        """
        other_partner = self.env.ref("base.res_partner_address_31")
        self._create_statement(amount=100, partner=other_partner)

        self.assertEqual(self.partner.customer_wallet_balance, 0)
        self.assertEqual(other_partner.customer_wallet_balance, -100)
