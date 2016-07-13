# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
import datetime
from lxml import etree


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    days_overdue = fields.Integer(compute='_compute_days_overdue',
                                  search='_search_days_overdue',
                                  string='Days overdue')
    overdue_term_1 = fields.Float(string='Overdue Term 1',
                                  compute='_compute_overdue_terms')
    overdue_term_2 = fields.Float(string='Overdue Term 2',
                                  compute='_compute_overdue_terms')
    overdue_term_3 = fields.Float(string='Overdue Term 3',
                                  compute='_compute_overdue_terms')
    overdue_term_4 = fields.Float(string='Overdue Term 4',
                                  compute='_compute_overdue_terms')
    overdue_term_5 = fields.Float(string='Overdue Term 5',
                                  compute='_compute_overdue_terms')

    @api.multi
    @api.depends('date_maturity')
    def _compute_days_overdue(self):
        today_date = fields.Date.from_string(fields.Date.today())
        for line in self:
            if line.date_maturity and line.amount_residual:
                date_maturity = fields.Date.from_string(
                    line.date_maturity)
                days_overdue = (today_date - date_maturity).days
                if days_overdue > 0:
                    line.days_overdue = days_overdue

    def _search_days_overdue(self, operator, value):
        due_date = fields.Date.from_string(fields.Date.today()) - \
                   datetime.timedelta(days=value)
        if operator in ('!=', '<>', 'in', 'not in'):
            raise ValueError('Invalid operator: %s' % (operator,))
        if operator == '>':
            operator = '<'
        elif operator == '<':
            operator = '>'
        elif operator == '>=':
            operator = '<='
        elif operator == '<=':
            operator = '>='
        return [('date_maturity', operator, due_date)]

    @api.multi
    @api.depends('date_maturity')
    def _compute_overdue_terms(self):
        today_date = fields.Date.from_string(fields.Date.today())
        company = self.env.user.company_id
        for line in self:
            line.overdue_term_1 = 0.0
            line.overdue_term_2 = 0.0
            line.overdue_term_3 = 0.0
            line.overdue_term_4 = 0.0
            line.overdue_term_5 = 0.0

            if line.date_maturity and line.amount_residual:
                date_maturity = fields.Date.from_string(
                    line.date_maturity)
                t1 = company.overdue_term_1
                t2 = company.overdue_term_2
                t3 = company.overdue_term_3
                t4 = company.overdue_term_4


                days_overdue = (today_date - date_maturity).days

                if t1 > days_overdue > 0 and t1:
                    line.overdue_term_1 = line.amount_residual
                elif t2 > days_overdue > t1 and t2:
                    line.overdue_term_2 = line.amount_residual
                elif t3 > days_overdue > t2 and t3:
                    line.overdue_term_3 = line.amount_residual
                elif t4 > days_overdue > t3 and t4:
                    line.overdue_term_4 = line.amount_residual
                elif days_overdue > t4 and t4:
                    line.overdue_term_5 = line.amount_residual
                elif days_overdue > 0:
                    line.overdue_term_5 = line.amount_residual

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        result = super(AccountMoveLine, self).fields_view_get(view_id,
                                                              view_type,
                                                              toolbar=toolbar,
                                                              submenu=submenu)
        doc = etree.XML(result['arch'])
        if result['model'] == 'account.move.line' and result['type'] == 'tree':
            company = self.env.user.company_id
            if 'overdue_term_1' in result['fields']:
                t1 = company.overdue_term_1
                if not t1:
                    for node in doc.xpath("//field[@name='overdue_term_1']"):
                        doc.remove(node)

                else:
                    result['fields']['overdue_term_1']['string'] = \
                        _('1-%d') % t1
            if 'overdue_term_2' in result['fields']:
                t1 = company.overdue_term_1
                t2 = company.overdue_term_2
                if not t2:
                    for node in doc.xpath("//field[@name='overdue_term_2']"):
                        doc.remove(node)
                else:
                    interval = ('%d-%d' % (int(t1)+1, t2))
                    result['fields']['overdue_term_2']['string'] = interval
            if 'overdue_term_3' in result['fields']:
                t2 = company.overdue_term_2
                t3 = company.overdue_term_3
                if not t3:
                    for node in doc.xpath("//field[@name='overdue_term_3']"):
                        doc.remove(node)
                else:
                    interval = ('%d-%d' % (int(t2)+1, t3))
                    result['fields']['overdue_term_3']['string'] = interval
            if 'overdue_term_4' in result['fields']:
                t3 = company.overdue_term_3
                t4 = company.overdue_term_4
                if not t4:
                    for node in doc.xpath("//field[@name='overdue_term_4']"):
                        doc.remove(node)
                else:
                    interval = ('%d-%d' % (int(t3) + 1, t4))
                    result['fields']['overdue_term_4']['string'] = interval
            if 'overdue_term_5' in result['fields']:
                t_last = company.overdue_term_4 or company.overdue_term_3 or\
                         company.overdue_term_2 or company.overdue_term_1
                interval = '+%d' % (int(t_last) + 1)
                result['fields']['overdue_term_5']['string'] = interval
            result['arch'] = etree.tostring(doc)
        return result
