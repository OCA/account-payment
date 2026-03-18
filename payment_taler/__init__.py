# SPDX-FileCopyrightText: 2025 Mael Panouillot <panouillot.mael@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from odoo.addons.payment import setup_provider, reset_payment_provider

from . import models
from . import controllers

def post_init_hook(env):
    setup_provider(env, 'taler')


def uninstall_hook(env):
    reset_payment_provider(env, 'taler')
