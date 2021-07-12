# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade
from psycopg2 import sql


def convert_field_to_two_characters(env, field_name):
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """
        UPDATE res_partner_holiday
        SET {field_name} = CONCAT('0', {field_name})
        WHERE length({field_name}) = 1
        """
        ).format(field_name=field_name),
    )


@openupgrade.migrate()
def migrate(env, version):
    convert_field_to_two_characters(env, sql.Identifier("month_from"))
    convert_field_to_two_characters(env, sql.Identifier("month_to"))
