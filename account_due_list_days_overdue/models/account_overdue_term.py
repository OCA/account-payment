# -*- coding: utf-8 -*-
# © 2016 Eficent Business and IT Consulting Services S.L. (
# <http://www.eficent.com>).
# © 2016 Therp BV (<http://therp.nl>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.modules.registry import RegistryManager
from openerp import exceptions


class AccountDaysOverdue(models.Model):
    _name = 'account.overdue.term'
    _description = 'Account Overdue Term'

    name = fields.Char(size=10, required=True)
    from_day = fields.Integer(string='From day', required=True)
    to_day = fields.Integer(string='To day', required=True)
    tech_name = fields.Char('Technical name', readonly=True,
                            compute='_compute_technical_name', store=True)

    @api.multi
    @api.depends('from_day', 'to_day')
    def _compute_technical_name(self):
        for rec in self:
            rec.tech_name = 'overdue_term_%d_%d' % (rec.from_day, rec.to_day)

    @api.model
    def create(self, vals):
        res = super(AccountDaysOverdue, self).create(vals)
        if self.pool['account.move.line']._register_hook(self.env.cr):
            RegistryManager.signal_registry_change(
                self.env.cr.dbname)
        return res

    @api.multi
    def write(self, vals):
        res = super(AccountDaysOverdue, self).write(vals)
        if self.pool['account.move.line']._register_hook(self.env.cr):
            RegistryManager.signal_registry_change(
                self.env.cr.dbname)
        return res

    @api.multi
    @api.constrains('from_day', 'to_day')
    def check_overlap(self):
        """Check that overdue terms do not overlap
        """
        for rec in self:
            date_domain = [
                ('from_day', '<=', rec.to_day),
                ('to_day', '>=', rec.from_day)]

            overlap = self.search(date_domain + [('id', '!=', self.id)])

            if overlap:
                raise exceptions.ValidationError(
                    _('Overdue Term %s overlaps with %s') %
                    (rec.name, overlap[0].name))
