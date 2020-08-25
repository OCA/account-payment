from odoo import _
from odoo.exceptions import ValidationError


class SlimpayPartnerFieldError(ValidationError):

    def __init__(self, fieldname, msg):
        self.fieldname = fieldname
        self.msg = msg
        self.name = _("Error with partner's %s.") % self.fieldname
        self.args = (self.fieldname, self.msg)
