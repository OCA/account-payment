# Copyright 2022 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.addons.account_customer_wallet.tests.common import TestBalance


class TestPosBalance(TestBalance):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

    def _create_statement(self, amount=0, partner=None):
        if partner is None:
            partner = self.partner

        self.env["account.bank.statement"].create(
            {
                "journal_id": self.customer_wallet_journal.id,
                "state": "open",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Name",
                            "amount": amount,
                            "partner_id": partner.id,
                        },
                    ),
                ],
            }
        )
