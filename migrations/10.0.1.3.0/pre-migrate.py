from odoo import SUPERUSER_ID
from odoo.api import Environment


def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    env.ref('commown.address').unlink()
    env.ref('payment_slimpay.address').unlink()
