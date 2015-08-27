##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from dateutil.relativedelta import relativedelta
from openerp import models, fields, api, exceptions, _
import calendar


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        """This method can't be new API due to arguments names are not
        standard for the API wrapper.
        """
        result = super(AccountPaymentTerm, self).compute(
            cr, uid, id, value=value, date_ref=date_ref, context=context)
        payment_term = self.browse(cr, uid, id, context=context)
        if not result:
            return result
        for i, line in enumerate(payment_term.line_ids):
            if not line.payment_days:
                continue
            payment_days = line._decode_payment_days(line.payment_days)
            if not payment_days:
                continue
            payment_days.sort()
            new_date = None
            date = fields.Date.from_string(result[i][0])
            days_in_month = calendar.monthrange(date.year, date.month)[1]
            for day in payment_days:
                if date.day <= day:
                    if day > days_in_month:
                        day = days_in_month
                    new_date = date + relativedelta(day=day)
                    break
            if not new_date:
                day = payment_days[0]
                if day > days_in_month:
                    day = days_in_month
                new_date = date + relativedelta(day=day, months=1)
            result[i] = (fields.Date.to_string(new_date), result[i][1])
        return result


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    def _decode_payment_days(self, days_char):
        # Admit space, dash and comma as separators
        days_char = days_char.replace(' ', '-').replace(',', '-')
        days_char = [x.strip() for x in days_char.split('-') if x]
        days = [int(x) for x in days_char]
        days.sort()
        return days

    @api.one
    @api.constrains('payment_days')
    def _check_payment_days(self):
        if not self.payment_days:
            return
        try:
            payment_days = self._decode_payment_days(self.payment_days)
            error = any(day <= 0 or day > 31 for day in payment_days)
        except:
            error = True
        if error:
            raise exceptions.Warning(
                _('Payment days field format is not valid.'))

    payment_days = fields.Char(
        string='Payment day(s)',
        help="Put here the day or days when the partner makes the payment. "
             "Separate each possible payment day with dashes (-), commas (,) "
             "or spaces ( ).")
