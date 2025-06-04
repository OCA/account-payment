# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def assign_check_date(env):
    payments = env["account.payment"].search([])
    for payment in payments:
        payment.write({"check_date": payment.date})
