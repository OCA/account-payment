# Copyright 2017 Tecnativa - Carlos Roca
from .common import AccountCheckPrintingReportBaseCommon


class TestNum2WordsLangSolution(AccountCheckPrintingReportBaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.propissory_note_amount = cls.env[
            "report.account_check_printing_report_base.promissory_footer_a4"
        ]
        cls.amount = 3.09

    def test_01_num2words_es_correction(self):
        amount_in_word = self.propissory_note_amount.with_context(
            lang="es"
        ).amount2words(self.amount)
        self.assertEqual("tres euros con nueve céntimos", amount_in_word)
        amount_in_word_stars = self.propissory_note_amount.fill_stars(amount_in_word)
        stars = "*" * (100 - len(amount_in_word))
        self.assertEqual(amount_in_word_stars, amount_in_word + " " + stars)

    def test_02_num2words_normal_flux(self):
        amount_in_word = self.propissory_note_amount.amount2words(self.amount)
        self.assertEqual("three euro, nine cents", amount_in_word)
        amount_in_word_stars = self.propissory_note_amount.fill_stars(amount_in_word)
        stars = "*" * (100 - len(amount_in_word))
        self.assertEqual(amount_in_word_stars, amount_in_word + " " + stars)
