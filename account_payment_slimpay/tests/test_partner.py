from ..exceptions import SlimpayPartnerFieldError

from odoo.tests.common import TransactionCase, at_install, post_install


@at_install(False)
@post_install(True)
class PartnerTC(TransactionCase):

    def partner_data(self, **kwargs):
        fr = self.env['res.country'].search([('code', '=', 'FR')])
        data = {'firstname': 'F', 'lastname': 'C', 'country_id': fr.id}
        data.update(kwargs)
        return data

    def test_zip(self):
        'Zip must have 5 figures when country is France'
        p = self.env['res.partner'].create(self.partner_data(zip='67000'))
        with self.assertRaises(SlimpayPartnerFieldError):
            p.update({'zip': '0'})

    def test_zip_no_country(self):
        'Zip is only checked when country is France'
        self.env['res.partner'].create(
            self.partner_data(zip='0', country_id=False))

    def test_slimpay_checks(self):
        '`slimpay_checks` must return a dict of errors like {attr: error_msg}'
        partner_model = self.env['res.partner']
        self.assertEqual(
            partner_model.slimpay_checks(self.partner_data(zip='67000')),
            {})
        self.assertEqual(
            partner_model.slimpay_checks(self.partner_data(zip='0')),
            {'zip': 'Incorrect zip code (should be 5 figures)'})
