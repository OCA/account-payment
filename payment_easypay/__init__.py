# Copyright 2025 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from . import controllers
from . import models

from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(env):
    """Set up the EasyPay provider after module installation."""
    setup_provider(env, "easypay")


def uninstall_hook(env):
    """Clean up the EasyPay provider before module uninstallation."""
    reset_payment_provider(env, "easypay")
