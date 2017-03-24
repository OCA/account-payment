# -*- coding: utf-8 -*-
# © 2016 Eficent Business and IT Consulting Services, S.L.
#   (<http://www.eficent.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.account_due_list.init_hook import \
    store_field_stored_invoice_id
from openerp.addons.account_due_list.init_hook import \
    store_field_invoice_user_id


def migrate(cr, version):
    if not version:
        return
    store_field_stored_invoice_id(cr)
    store_field_invoice_user_id(cr)
