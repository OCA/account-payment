import regex  # not re: we use unicode properties

from odoo import api, models, _

from ..exceptions import SlimpayPartnerFieldError


class SlimpayPartner(models.Model):
    _inherit = 'res.partner'

    SLIMPAY_NAME_RE = regex.compile(u'^[\p{L} -]+$')
    SLIMPAY_FR_ZIP = regex.compile(u'^[0-9]{5}+$')

    @api.model
    def _slimpay_check_name_field(self, fieldname, value):
        """Check slimpay validity regarding partner's first- or last- name
        (`fieldname` being one of "firstname", "lastname").
        """
        if not self.SLIMPAY_NAME_RE.match(value):
            msg = _('%(field)s must contain only letters, spaces and "-"')
            raise SlimpayPartnerFieldError(fieldname,
                                           msg % {'field': _(fieldname)})

    @api.model
    def _slimpay_check_firstname(self, value, **kw):
        """Raise a `SlimpayPartnerFieldError` if given firstname `value` is not
        valid for Slimpay.
        """
        self._slimpay_check_name_field('firstname', value)

    @api.model
    def _slimpay_check_lastname(self, value, **kw):
        """Raise a `SlimpayPartnerFieldError` if given lastname `value` is not
        valid for Slimpay.
        """
        self._slimpay_check_name_field('lastname', value)

    @api.model
    def _slimpay_check_zip(self, value, country_id=None, **kw):
        """Raise a `SlimpayPartnerFieldError` if given zip `value` is not
        suitable as a Slimpay zip code for country of id `country_id`
        (only restrictive for France).

        """
        try:
            country_id = int(country_id)
        except:
            return
        country = self.env['res.country'].browse(int(country_id))
        if country.code == 'FR':
            if not self.SLIMPAY_FR_ZIP.match(value):
                raise SlimpayPartnerFieldError(
                    'zip', _('Incorrect zip code (should be 5 figures)'))

    @api.model
    def slimpay_checks(self, values):
        """Validate proposed `values` as partner fields.

        Given a proposed dict of field `values` return a dict of
        errors, if any, for fields that have a slimpay validation
        rule, under the form::
            {'field name': 'error message'}
        """
        errors = {}
        for fieldname in values:
            checker = getattr(self, '_slimpay_check_%s' % fieldname, None)
            if checker is not None:
                try:
                    checker(values[fieldname], **values)
                except SlimpayPartnerFieldError as exc:
                    errors[fieldname] = exc.msg
        return errors

    @api.constrains("firstname")
    def _slimpay_firstname_constraint(self):
        """Ensure firstname is valid for slimpay."""
        for rec in self:
            if not rec.is_company:
                self._slimpay_check_firstname(rec.firstname or u'')

    @api.constrains("lastname")
    def _slimpay_lastname_constraint(self):
        """Ensure lastname is valid for slimpay."""
        for rec in self:
            if not rec.is_company:
                self._slimpay_check_lastname(rec.lastname or u'')

    @api.constrains("zip")
    def _slimpay_zip_constraint(self):
        """Ensure zipcode is valid for slimpay (when in France)."""
        for rec in self:
            if not rec.is_company:
                self._slimpay_check_zip(rec.zip, country_id=rec.country_id.id)
