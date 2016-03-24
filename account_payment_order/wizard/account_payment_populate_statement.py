# -*- coding: utf-8 -*-
# (c) 2015 brain-tec AG (http://www.braintec-group.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from openerp import models, fields, api, _

class AccountPaymentPopulateStatement(models.TransientModel):
    _name = "account.payment.populate.statement"
    _description = "Account Payment Populate Statement"

    lines = fields.Many2many('payment.line', string='Payment Lines')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        line_obj = self.env['payment.line']

        res = super(AccountPaymentPopulateStatement, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=submenu)
        lines = line_obj.search([
            ('move_line_id.full_reconcile_id', '=', False),
            ('bank_statement_line_id', '=', False)])
        lines += line_obj.search([
            ('move_line_id.full_reconcile_id', '=', False),
            ('order_id.mode', '=', False)])

        domain = '[("id", "in", '+ str(lines.ids)+')]'
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='lines']")
        for node in nodes:
            node.set('domain', domain)
        res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def populate_statement(self):
        self.ensure_one()
        statement_obj = self.env['account.bank.statement']
        statement_line_obj = self.env['account.bank.statement.line']
        currency_obj = self.env['res.currency']

        if not self.lines:
            return {'type': 'ir.actions.act_window_close'}

        statement = statement_obj.search([('id','=',
                                           self.env.context['active_id'])])

        for line in self.lines:
            ctx = self.env.context.copy()
            ctx['date'] = line.ml_maturity_date
            amount = line.with_context(ctx).\
                currency_id.compute(line.amount_currency,statement.currency_id)

            st_line_vals = self._prepare_statement_line_vals(line, amount, statement)
            st_line_id = statement_line_obj.create(st_line_vals)
            line.bank_statement_line_id = st_line_id.id
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_statement_line_vals(self,payment_line, amount,statement):
        return {
            'name': payment_line.order_id.reference or '?',
            'amount':-amount,
            'partner_id': payment_line.partner_id.id,
            'statement_id': statement.id,
            'ref': payment_line.communication,
        }