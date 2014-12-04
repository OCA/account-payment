# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Eficent (<http://www.eficent.com/>)
#              Jordi Ballester Alomar <jordi.ballester@eficent.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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