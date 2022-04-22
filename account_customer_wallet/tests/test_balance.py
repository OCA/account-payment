# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from .common import TestBalance


class TestAccountBalance(TestBalance):
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

    def test_balance_to_parent(self):
        """Credit child partner should impact parent partner balance"""
        self._create_move(credit=1000)
        self.assertEqual(self.partner.customer_wallet_balance, 1000)
        self.assertEqual(self.partner.parent_id.customer_wallet_balance, 1000)

    def test_balance_to_child(self):
        """Credit parent partner should impact child partner balance"""
        self._create_move(credit=2000, partner=self.partner.parent_id)
        self.assertEqual(self.partner.customer_wallet_balance, 2000)
        self.assertEqual(self.partner.parent_id.customer_wallet_balance, 2000)

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

    def test_no_wallet_account(self):
        """If no wallet account is set, expect balances to be zero."""
        self._create_move(credit=100)

        self.company_id.customer_wallet_account_id = None

        self.assertFalse(self.company_id.is_enabled_customer_wallet)
        self.assertEqual(self.partner.customer_wallet_balance, 0)
