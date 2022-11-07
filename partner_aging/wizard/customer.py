# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models, tools


class PartnerAgingDate(models.TransientModel):
    _name = "partner.aging.date"
    _description = "Partner Aging Date"

    age_date = fields.Datetime(
        string="Aging Date", required=True, default=lambda self: fields.Datetime.now()
    )

    def open_partner_aging(self):
        ctx = self._context.copy()
        age_date = self.age_date
        ctx.update({"age_date": age_date})

        customer_aging = self.env["partner.aging.customer.ad"]

        query = """
                SELECT
                aml.id,
                aml.partner_id as partner_id,
                ai.invoice_user_id as salesman,
                aml.date as date,
                aml.date_maturity as date_due,
                ai.name as invoice_ref,
                days_due AS avg_days_overdue,
                CASE WHEN (days_due <= 0) THEN
                        CASE WHEN
                        (aml.full_reconcile_id is NULL and\
                         aml.amount_residual<0) THEN -(aml.credit-\
                         (select coalesce(sum(apr.amount),0) \
                         from account_partial_reconcile apr\
                          where (apr.credit_move_id =aml.id or \
                          apr.debit_move_id=aml.id) and \
                          apr.max_date <= '%s'))
                        WHEN
                        (aml.full_reconcile_id is NULL and\
                        aml.amount_residual>0) THEN aml.debit-\
                        (select coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where\
                        (apr.credit_move_id =aml.id or apr.debit_move_id\
                        =aml.id) and apr.max_date <= '%s')
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) THEN \
                        aml.amount_residual END ELSE 0 END AS not_due,
                CASE WHEN (days_due BETWEEN 1 and 30) THEN
                    CASE WHEN
                    (aml.full_reconcile_id is NULL and aml.\
                    amount_residual<0) THEN -(aml.credit-(select coalesce(\
                    sum(apr.amount),0) from account_partial_reconcile apr \
                    where (apr.credit_move_id =aml.id or apr.debit_move_id=\
                    aml.id) and apr.max_date <= '%s'))
                        WHEN
                        (aml.full_reconcile_id is NULL and aml.amount_residual\
                        >0) THEN aml.debit-(select coalesce(sum(apr.amount),0)\
                         from account_partial_reconcile apr where \
                         (apr.credit_move_id =aml.id or apr.debit_move_id\
                         =aml.id) and apr.max_date <= '%s')
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) THEN \
                        aml.amount_residual END ELSE 0 END AS days_due_01to30,

                CASE WHEN (days_due BETWEEN 31 and 60) THEN
                    CASE WHEN
                    (aml.full_reconcile_id is NULL and aml.\
                    amount_residual<0) THEN -(aml.credit-(select coalesce(\
                    sum(apr.amount),0) from account_partial_reconcile apr \
                    where (apr.credit_move_id =aml.id or apr.debit_move_id=\
                    aml.id) and apr.max_date <= '%s'))
                        WHEN
                        (aml.full_reconcile_id is NULL and aml.amount_residual\
                        >0) THEN aml.debit-(select coalesce(sum(apr.amount),0)\
                         from account_partial_reconcile apr where \
                         (apr.credit_move_id =aml.id or apr.debit_move_id\
                         =aml.id) and apr.max_date <= '%s')
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) THEN \
                        aml.amount_residual END ELSE 0 END AS days_due_31to60,
                CASE WHEN (days_due BETWEEN 61 and 90) THEN
                    CASE WHEN
                    (aml.full_reconcile_id is NULL and \
                    aml.amount_residual<0) THEN -(aml.credit-(select coalesce(\
                    sum(apr.amount),0) from account_partial_reconcile apr \
                    where (apr.credit_move_id =aml.id or apr.debit_move_id=\
                    aml.id) and apr.max_date <= '%s'))
                        WHEN
                         (aml.full_reconcile_id is NULL and aml.\
                         amount_residual>0) THEN aml.debit-\
                         (select coalesce(sum(apr.amount),0) \
                         from account_partial_reconcile apr where \
                         (apr.credit_move_id =aml.id or apr.debit_move_id\
                         =aml.id) and apr.max_date <= '%s')
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) \
                        THEN aml.amount_residual END ELSE 0 END\
                         AS days_due_61to90,
                CASE WHEN (days_due BETWEEN 91 and 120) THEN
                        CASE WHEN
                        (aml.full_reconcile_id is NULL and\
                         aml.amount_residual<0) THEN -(aml.credit-\
                         (select coalesce(sum(apr.amount),0) \
                         from account_partial_reconcile apr where \
                         (apr.credit_move_id =aml.id or apr.debit_move_id\
                         =aml.id) and apr.max_date <= '%s'))
                        WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual>0) THEN aml.debit-\
                        (select coalesce(sum(apr.amount),0) from \
                        account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or apr.debit_move_id\
                        =aml.id) and apr.max_date <= '%s')
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) \
                        THEN aml.amount_residual END ELSE 0 END AS\
                         days_due_91to120,
                CASE WHEN (days_due >= 121) THEN
                        CASE WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual<0) THEN -(aml.credit-\
                        (select coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or apr.debit_move_id\
                        =aml.id) and apr.max_date <= '%s'))
                        WHEN (aml.full_reconcile_id is NULL and \
                        aml.amount_residual>0) THEN aml.debit-\
                        (select coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or apr.debit_move_id\
                        =aml.id) and apr.max_date <= '%s')
                        WHEN (aml.full_reconcile_id is NOT NULL) THEN\
                         aml.amount_residual END ELSE 0 END AS\
                          days_due_121togr,
                CASE when days_due < 0 THEN 0 ELSE days_due END\
                 as "max_days_overdue",
                CASE WHEN (aml.full_reconcile_id is NULL and\
                 aml.amount_residual<0) THEN -(aml.credit-\
                 (select coalesce(sum(apr.amount),0) from \
                 account_partial_reconcile apr where \
                 (apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)\
                  and apr.max_date <= '%s'))
                    WHEN
                    (aml.full_reconcile_id is NULL and \
                    aml.amount_residual>0) THEN aml.debit-\
                    (select coalesce(sum(apr.amount),0) \
                    from account_partial_reconcile apr where \
                    (apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)\
                     and apr.max_date <= '%s')
                     WHEN
                     (aml.full_reconcile_id is NOT NULL) THEN \
                     aml.amount_residual END AS total,
                ai.id as invoice_id,
                ai.invoice_date_due as inv_date_due
                FROM account_move_line aml
                INNER JOIN
                  (
                   SELECT lt.id,
                   CASE WHEN inv.id is null THEN \
                       current_date - lt.date_maturity
                        WHEN inv.id is not null \
                            THEN '%s' - inv.invoice_date_due
                        ELSE current_date - lt.date END AS days_due
                   FROM account_move_line lt LEFT JOIN account_move inv on\
                    lt.move_id = inv.id
                ) DaysDue
                ON DaysDue.id = aml.id
                LEFT JOIN account_move as ai ON ai.id = aml.move_id
                LEFT JOIN account_account as account ON \
                    account.id = aml.account_id
                WHERE
                account.user_type_id in \
                    (select id from account_account_type where\
                 type = 'receivable')
                and aml.date <='%s'
                and aml.amount_residual!=0
                GROUP BY aml.partner_id, aml.id, ai.name, days_due,\
                 ai.invoice_user_id, ai.id
              """ % (
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
        tools.drop_view_if_exists(
            self.env.cr, "%s" % (customer_aging._name.replace(".", "_"))
        )
        # pylint: disable=sql-injection
        self.env.cr.execute(
            """
                CREATE OR REPLACE VIEW %s AS ( %s)
        """
            % (customer_aging._name.replace(".", "_"), query)
        )

        return {
            "name": _("Customer Aging"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "partner.aging.customer.ad",
            "type": "ir.actions.act_window",
            "domain": [("total", "!=", 0)],
            "context": ctx,
        }


class AccountAgingCustomerAD(models.Model):
    _name = "partner.aging.customer.ad"
    _description = "Partner Aging Customer AD"
    _order = "partner_id"
    _rec_name = "partner_id"
    _auto = False

    def docopen(self):
        """
        @description  Open document (invoice or payment) related to the
                      unapplied payment or outstanding balance on this line
        """

        # Get this line's invoice id
        inv_id = self.id
        # if this is an unapplied payment
        # (all unapplied payments hard-coded to -999),
        # get the referenced voucher
        if inv_id == -999:
            payment_pool = self.env["account.move"]
            # Get referenced customer payment (invoice_ref field is actually a
            # -payment for these)
            move_id = payment_pool.search([("name", "=", self.invoice_ref)])[0]
            # Set values for form
            view_id = self.env.ref("account.view_move_form").id or False
            name = "Customer Payments"
            res_model = "account.move"
            ctx = "{}"
            doc_id = move_id
        # otherwise get the invoice
        else:
            view_id = self.env.ref("account.view_move_form").id or False
            name = "Customer Invoices"
            res_model = "account.move"
            ctx = "{'type':'out_invoice'}"
            doc_id = inv_id
        if not doc_id:
            return {}
        # Open up the document's form
        return {
            "name": _(name),
            "view_type": "form",
            "view_mode": "form",
            "view_id": [view_id],
            "res_model": res_model,
            "context": ctx,
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "target": "current",
            "res_id": doc_id,
        }

    partner_id = fields.Many2one("res.partner", "Partner", readonly=True)
    avg_days_overdue = fields.Integer(readonly=True)
    date = fields.Date(readonly=True)
    date_due = fields.Date("Due Date", readonly=True)
    inv_date_due = fields.Date("Invoice Date", readonly=True)
    total = fields.Float(readonly=True)
    not_due = fields.Float("Current", readonly=True)
    days_due_01to30 = fields.Float("1/30", readonly=True)
    days_due_31to60 = fields.Float("31/60", readonly=True)
    days_due_61to90 = fields.Float("61/90", readonly=True)
    days_due_91to120 = fields.Float("91/120", readonly=True)
    days_due_121togr = fields.Float("+121", readonly=True)
    max_days_overdue = fields.Integer("Days Outstanding", readonly=True)
    invoice_ref = fields.Char("Our Invoice", size=25, readonly=True)
    invoice_id = fields.Many2one("account.move", "Invoice", readonly=True)
    salesman = fields.Many2one("res.users", "Sales Rep", readonly=True)

    def init(self):
        cr = self._cr
        query = """
                SELECT
                aml.id,
                aml.partner_id as partner_id,
                ai.invoice_user_id as salesman,
                aml.date as date,
                aml.date_maturity as date_due,
                ai.name as invoice_ref,
                days_due AS avg_days_overdue, 0 as days_due_01to30,
                CASE WHEN (days_due BETWEEN 31 and 60) THEN
                    CASE WHEN (aml.full_reconcile_id is NULL and \
                    aml.amount_residual<0) THEN -(aml.credit-\
                    (select coalesce(sum(apr.amount),0) \
                    from account_partial_reconcile apr where \
                    (apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)\
                     and apr.max_date <= current_date))
                        WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual>0) THEN aml.debit-\
                        (select coalesce(sum(apr.amount),0) from\
                         account_partial_reconcile apr where \
                         (apr.credit_move_id =aml.id or \
                         apr.debit_move_id=aml.id) and apr.max_date\
                          <= current_date)
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) THEN \
                        aml.amount_residual END ELSE 0 END AS \
                        days_due_31to60,
                CASE WHEN (days_due BETWEEN 61 and 90) THEN
                    CASE WHEN
                    (aml.full_reconcile_id is NULL \
                    and aml.amount_residual<0) THEN -(aml.credit-(\
                    select coalesce(sum(apr.amount),0) \
                    from account_partial_reconcile apr where \
                    (apr.credit_move_id =aml.id or apr.debit_move_id=aml.id)\
                     and apr.max_date <= current_date))
                        WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual>0) THEN aml.debit-\
                        (select coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or \
                        apr.debit_move_id=aml.id) and apr.max_date \
                        <= current_date)
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) THEN \
                        aml.amount_residual END ELSE 0 END\
                         AS days_due_61to90,
                CASE WHEN (days_due BETWEEN 91 and 120) THEN
                        CASE WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual<0) THEN -(aml.credit-\
                        (select coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or apr.debit_move_id\
                        =aml.id) and apr.max_date <= current_date))
                        WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual>0) THEN aml.debit-(select \
                        coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or \
                        apr.debit_move_id=aml.id) and apr.max_date \
                        <= current_date)
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) THEN \
                        aml.amount_residual END ELSE 0 END AS days_due_91to120,
                CASE WHEN (days_due >= 121) THEN
                        CASE WHEN (aml.full_reconcile_id is NULL and \
                        aml.amount_residual<0) THEN -(aml.credit-(select \
                        coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or \
                        apr.debit_move_id=aml.id) and apr.max_date <=\
                         current_date))
                        WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual>0) THEN aml.debit-(select \
                        coalesce(sum(apr.amount),0) from \
                        account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or apr.debit_move_id\
                        =aml.id) and apr.max_date <= current_date)
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) THEN \
                        aml.amount_residual END ELSE 0 END AS days_due_121togr,
                CASE when days_due < 0 THEN 0 ELSE days_due END as\
                 "max_days_overdue",
                CASE WHEN (days_due < 31) THEN
                        CASE WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual<0) THEN -(aml.credit-(select \
                        coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or apr.debit_move_id\
                        =aml.id) and apr.max_date <= current_date))
                        WHEN
                        (aml.full_reconcile_id is NULL and \
                        aml.amount_residual>0) THEN aml.debit-(select \
                        coalesce(sum(apr.amount),0) \
                        from account_partial_reconcile apr where \
                        (apr.credit_move_id =aml.id or \
                        apr.debit_move_id=aml.id) and apr.max_date <=\
                         current_date)
                        WHEN
                        (aml.full_reconcile_id is NOT NULL) THEN \
                        aml.amount_residual END ELSE 0 END AS not_due,
                CASE WHEN (aml.full_reconcile_id is NULL and \
                aml.amount_residual<0) THEN -(aml.credit-(select \
                coalesce(sum(apr.amount),0) from account_partial_reconcile apr\
                 where (apr.credit_move_id =aml.id or apr.debit_move_id\
                 =aml.id) and apr.max_date <= current_date))
                    WHEN
                    (aml.full_reconcile_id is NULL and \
                    aml.amount_residual>0) THEN aml.debit-(select \
                    coalesce(sum(apr.amount),0) from account_partial_reconcile\
                     apr where (apr.credit_move_id =aml.id or \
                     apr.debit_move_id=aml.id) and apr.max_date \
                     <= current_date)
                     WHEN
                     (aml.full_reconcile_id is NOT NULL) THEN \
                     aml.amount_residual END AS total,
                ai.id as invoice_id,
                ai.invoice_date_due as inv_date_due
                FROM account_move_line aml
                INNER JOIN
                  (
                   SELECT lt.id,
                   CASE WHEN inv.id is null then
                   current_date - lt.date_maturity
                        WHEN inv.id is not null THEN \
                            current_date - inv.invoice_date_due
                        ELSE current_date - lt.date END AS days_due
                   FROM account_move_line lt LEFT JOIN account_move inv on\
                    lt.move_id = inv.id
                ) DaysDue
                ON DaysDue.id = aml.id
                LEFT JOIN account_move as ai ON ai.id = aml.move_id
                LEFT JOIN account_account as account ON \
                    account.id = aml.account_id
                WHERE
                account.user_type_id in (select id from account_account_type \
                    where type = 'receivable')
                and aml.date <=current_date
                and aml.amount_residual!=0
                GROUP BY aml.partner_id, aml.id, ai.name, days_due, \
                ai.invoice_user_id, ai.id
              """

        tools.drop_view_if_exists(cr, "%s" % (self._name.replace(".", "_")))
        # pylint: disable=sql-injection
        cr.execute(
            """
                      CREATE OR REPLACE VIEW %s AS ( %s)
        """
            % (self._name.replace(".", "_"), query)
        )
