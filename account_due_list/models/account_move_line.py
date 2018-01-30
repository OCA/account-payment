# © 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#        Jordi Esteve <jesteve@zikzakmedia.com>
# © 2011 Domsense srl (<http://www.domsense.com>)
# © 2011-2013 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2015 Andrea Cometa <info@andreacometa.it>
# © 2015 Eneko Lacunza <elacunza@binovo.es>
# © 2015 Tecnativa (http://www.tecnativa.com)
# © 2016 Eficent Business and IT Consulting Services S.L.
#        (http://www.eficent.com)
# © 2018 Ozono Multimedia S.L.L.
#        (http://www.ozonomultimedia.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_origin = fields.Char(related='invoice_id.origin',
                                 string='Source Doc')
    invoice_date = fields.Date(related='invoice_id.date_invoice',
                               string='Invoice Date')
    partner_ref = fields.Char(related='partner_id.ref', string='Partner Ref')
    payment_term_id = fields.Many2one('account.payment.term',
                                      related='invoice_id.payment_term_id',
                                      string='Payment Terms')
    stored_invoice_id = fields.Many2one(
        comodel_name='account.invoice', compute='_compute_invoice',
        string='Invoice', store=True)

    invoice_user_id = fields.Many2one(
        comodel_name='res.users', related='stored_invoice_id.user_id',
        string="Invoice salesperson", store=True)

    @api.multi
    @api.depends('move_id', 'invoice_id.move_id')
    def _compute_invoice(self):
        for line in self:
            invoices = self.env['account.invoice'].search(
                [('move_id', '=', line.move_id.id)])
            line.stored_invoice_id = invoices[:1]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        model_data_obj = self.env['ir.model.data']
        ids = model_data_obj.search([
            ('module', '=', 'account_due_list'),
            ('name', '=', 'view_payments_tree')])
        if ids:
            view_payments_tree_id = model_data_obj.get_object_reference(
                'account_due_list', 'view_payments_tree')
        if ids and view_id == view_payments_tree_id[1]:
            # Use due list
            result = super(models.Model, self).fields_view_get(
                view_id, view_type, toolbar=toolbar, submenu=submenu)
        else:
            # Use special views for account.move.line object
            # (for ex. tree view contains user defined fields)
            result = super(AccountMoveLine, self).fields_view_get(
                view_id, view_type, toolbar=toolbar, submenu=submenu)
        return result
