# -*- coding: utf-8 -*-
# © 2015 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from account_check_writing.report import check_print
from openerp.report import report_sxw

# remove previous report.account.print.check.top service :
from netsvc import Service
del Service._services['report.account.print.check.top']

# register the new report.account.print.check.top service :
report_sxw.report_sxw(
    'report.account.print.check.top',
    'account.voucher',
    'account_check_writing_remit_to/report/check_print_top.rml',
    parser=check_print.report_print_check, header=False
)

# remove previous report.account.print.check.middle service :
del Service._services['report.account.print.check.middle']
# register the new report.account.print.check.middle service :
report_sxw.report_sxw(
    'report.account.print.check.middle',
    'account.voucher',
    'account_check_writing_remit_to/report/check_print_middle.rml',
    parser=check_print.report_print_check, header=False
)

# remove previous report.account.print.check.bottom service :
del Service._services['report.account.print.check.bottom']
# register the new report.account.print.check.bottom service :
report_sxw.report_sxw(
    'report.account.print.check.bottom',
    'account.voucher',
    'account_check_writing_remit_to/report/check_print_bottom.rml',
    parser=check_print.report_print_check, header=False
)
