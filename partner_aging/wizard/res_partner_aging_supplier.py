# Copyright 2012 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools


class ResPartnerAgingSupplier(models.Model):
    _name = "res.partner.aging.supplier"
    _description = "Res Partner Aging Supplier"
    _auto = False
    _order = "partner_id"

    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    max_days_overdue = fields.Integer("Days Outstanding", readonly=True)
    avg_days_overdue = fields.Integer("Avg Days Overdue", readonly=True)
    date = fields.Date("Date", readonly=True)
    date_due = fields.Date("Due Date", readonly=True)
    inv_date_due = fields.Date("Invoice Date", readonly=True)
    total = fields.Float("Total", readonly=True)
    not_due = fields.Float("Not Due Yet", readonly=True)
    days_due_01to30 = fields.Float("1/30", readonly=True)
    days_due_31to60 = fields.Float("31/60", readonly=True)
    days_due_61to90 = fields.Float("61/90", readonly=True)
    days_due_91to120 = fields.Float("91/120", readonly=True)
    days_due_121togr = fields.Float("+121", readonly=True)
    invoice_ref = fields.Char("Their Invoice", size=25, readonly=True)
    invoice_id = fields.Many2one("account.move", "Invoice", readonly=True)
    salesman = fields.Many2one("res.users", "Sales Rep", readonly=True)

    def execute_aging_query(self, age_date=False):
        if not age_date:
            age_date = fields.Date.context_today(self)

        query = """
		SELECT aml.id, aml.partner_id as partner_id, ai.invoice_user_id as
		salesman, aml.date as date, aml.date as date_due, ai.name
		as invoice_ref, days_due AS avg_days_overdue,
		CASE WHEN (days_due BETWEEN 1 AND 30) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE
			(apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)
			AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(
			aml.debit-(select coalesce(sum(apr.amount),0)
			FROM account_partial_reconcile apr WHERE
			(apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_01to30,
		CASE WHEN (days_due BETWEEN 31 AND 60) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE
			(apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)
			AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(
			aml.debit-(select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE
			(apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_31to60,
		CASE WHEN (days_due BETWEEN 61 AND 90) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)
			AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(
			aml.debit-(select coalesce(sum(apr.amount),0)
			FROM account_partial_reconcile apr WHERE
			(apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_61to90,
		CASE WHEN (days_due BETWEEN 91 AND 120) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(
			aml.debit-(select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_91to120,
		CASE WHEN (days_due >= 121) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(
			aml.debit-(select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_121togr,
		CASE when days_due < 0 THEN 0 ELSE days_due END as
		"max_days_overdue",
		CASE WHEN (days_due < 31) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(aml.debit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS not_due,
		CASE WHEN (aml.full_reconcile_id is NULL AND
		aml.amount_residual<0) THEN aml.credit-(
		select coalesce(sum(apr.amount),0) FROM
		account_partial_reconcile apr WHERE (
		apr.credit_move_id =aml.id or apr.debit_move_id=aml.id) AND
		apr.create_date <= '{}')
		WHEN (aml.full_reconcile_id is NULL AND
		aml.amount_residual=0) THEN 0
		WHEN (aml.full_reconcile_id is NULL AND
		aml.amount_residual>0) THEN -(aml.debit-(
		select coalesce(sum(apr.amount),0) FROM
		account_partial_reconcile apr WHERE (
		apr.credit_move_id =aml.id or
		apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
		WHEN (aml.full_reconcile_id is NOT NULL) THEN
		aml.amount_residual END AS total,
		ai.id as invoice_id,
		ai.invoice_date_due as inv_date_due
		FROM account_move_line aml
		LEFT JOIN account_account ac ON ac.id = aml.account_id
		INNER JOIN
		  (
		   SELECT lt.id,
		   CASE WHEN inv.invoice_date_due is null THEN 0
		   WHEN inv.id is not null THEN '{}' - inv.invoice_date_due
		   ELSE current_date - lt.date END AS days_due
		   FROM account_move_line lt LEFT JOIN account_move inv ON
		   lt.move_id = inv.id
		) DaysDue
		ON DaysDue.id = aml.id
		LEFT JOIN account_move as ai ON ai.id = aml.move_id
		WHERE
		ac.user_type_id in (select id FROM account_account_type WHERE
		type = 'payable')
		AND aml.date <= '{}'
		AND ai.state = 'posted' AND
		(ai.payment_state != 'paid' OR
		aml.full_reconcile_id IS NULL)
		AND ai.move_type IN ('in_invoice' , 'in_refund')
		AND ai.partner_id IS NOT NULL
		GROUP BY aml.partner_id, aml.id, ai.name, days_due,
		ai.invoice_user_id, ai.id
		UNION
		SELECT aml.id, aml.partner_id as partner_id, ai.invoice_user_id as
		salesman, aml.date as date, aml.date as date_due, ai.name as
		invoice_ref, days_due AS avg_days_overdue,
		CASE WHEN (days_due BETWEEN 1 AND 30) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or apr.debit_move_id=aml.id
			) AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(aml.debit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_01to30,
		CASE WHEN (days_due BETWEEN 31 AND 60) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)
			AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(aml.debit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_31to60,
		CASE WHEN (days_due BETWEEN 61 AND 90) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or apr.debit_move_id=aml.id
			) AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(aml.debit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_61to90,
		CASE WHEN (days_due BETWEEN 91 AND 120) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(aml.debit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_91to120,
		CASE WHEN (days_due >= 121) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE
			(apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(aml.debit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS days_due_121togr,
		CASE when days_due < 0 THEN 0 ELSE days_due END as
		"max_days_overdue",
		CASE WHEN (days_due < 31) THEN
			CASE WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual<0) THEN aml.credit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}')
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual=0) THEN 0
			WHEN (aml.full_reconcile_id is NULL AND
			aml.amount_residual>0) THEN -(aml.debit-(
			select coalesce(sum(apr.amount),0) FROM
			account_partial_reconcile apr WHERE (
			apr.credit_move_id =aml.id or
			apr.debit_move_id=aml.id) AND apr.create_date <= '{}'))
			WHEN (aml.full_reconcile_id is NOT NULL) THEN
			aml.amount_residual END ELSE 0 END AS not_due,
		CASE WHEN (aml.full_reconcile_id is NULL AND
		aml.amount_residual<0) THEN aml.credit-(
		select coalesce(sum(apr.amount),0) FROM
		account_partial_reconcile apr WHERE (
		apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)
		AND apr.create_date <= '{}')
		WHEN (aml.full_reconcile_id is NULL AND
		aml.amount_residual=0) THEN 0
		WHEN (aml.full_reconcile_id is NULL AND
		aml.amount_residual>0) THEN -(aml.debit-(
		select coalesce(sum(apr.amount),0) FROM
		account_partial_reconcile apr WHERE (
		apr.credit_move_id =aml.id or apr.debit_move_id=aml.id
		) AND apr.create_date <= '{}'))
		WHEN (aml.full_reconcile_id is NOT NULL) THEN
		aml.amount_residual END AS total,
		ai.id as invoice_id,
		ai.invoice_date_due as inv_date_due
		FROM account_move_line aml
		LEFT JOIN account_account ac ON ac.id = aml.account_id
		INNER JOIN
		  (
		   SELECT lt.id,
		   CASE WHEN inv.invoice_date_due is null THEN 0
		   WHEN inv.id is not null THEN '{}' - inv.invoice_date_due
		   ELSE current_date - lt.date END AS days_due
		   FROM account_move_line lt LEFT JOIN account_move inv ON
		   lt.move_id = inv.id
		) DaysDue
		ON DaysDue.id = aml.id
		LEFT JOIN account_move as ai ON ai.id = aml.move_id
		WHERE
		ac.user_type_id in (select id FROM account_account_type WHERE
		type = 'payable')
		AND aml.date <= '{}'
		AND aml.partner_id IS NULL 
		AND ai.partner_id IS NOT NULL
		AND aml.full_reconcile_id is NULL
		GROUP BY aml.partner_id, aml.id, ai.name, days_due,
		ai.invoice_user_id, ai.id
		UNION
		select aml.id,
			aml.partner_id as partner_id,
			aml.create_uid as salesman,
			aml.date as date,
			aml.date as date_due,
			' ' as invoice_ref,
			0 as avg_days_overdue,
			0 as days_due_01to30,
			0 as days_due_31to60,
			0 as days_due_61to90,
			0 as days_due_91to120,
			0 as days_due_121togr,
			0 as max_days_overdue,
			0 as not_due,
		CASE WHEN (aml.debit - (select sum(credit) FROM
			account_move_line l WHERE
			l.full_reconcile_id = aml.full_reconcile_id
			AND l.date<='{}')) > 0 
			THEN -(aml.debit - (select sum(credit) FROM
			account_move_line l WHERE
			l.full_reconcile_id = aml.full_reconcile_id AND l.date<='{}'))
			ELSE 0 END AS total,
		null as invoice_id,
		aml.date as inv_date_due
		FROM account_move_line aml
		WHERE aml.date <= '{}'
		AND aml.full_reconcile_id IS NOT NULL
		AND aml.account_id in (select id FROM account_account_type
		WHERE type = 'payable')
		AND aml.debit > 0
              """.format(
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
            age_date,
        )

        tools.drop_view_if_exists(self.env.cr, self._table)
        # pylint: disable=sql-injection
        q = """CREATE OR REPLACE VIEW {} AS ({})""".format(self._table, (query))
        self.env.cr.execute(q)

    def open_document(self):
        """
        @description  Open form view of Supplier Invoice
        """
        xmlid = "account.action_move_in_invoice_type"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
        action["res_id"] = self.invoice_id.id
        return action

    def init(self):
        self.execute_aging_query()
        super(ResPartnerAgingSupplier, self).init()
