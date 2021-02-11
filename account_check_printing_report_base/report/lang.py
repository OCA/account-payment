# pylint: disable=missing-import-error
from num2words import CONVERTER_CLASSES, CONVERTES_TYPES, num2words
from num2words.base import Num2Word_Base
from num2words.lang_ES import Num2Word_ES

num2words_by_lang = {"es": "Num2WordESCustom"}


class Num2WordESCustom(Num2Word_ES):
    CURRENCY_FORMS = Num2Word_ES.CURRENCY_FORMS.copy()
    CURRENCY_FORMS.update({"EUR": (("euro", "euros"), ("céntimo", "céntimos"))})

    # TODO: PR to remove overwrite in num2words code and use CURRENCY_FORMS
    def to_currency(self, val, longval=True, old=False):
        return Num2Word_Base.to_currency(
            self, val, currency="EUR", cents=True, seperator=" con", adjective=False
        )


def num2words_custom(number, ordinal=False, lang="en", to="cardinal", **kwargs):
    if lang not in CONVERTER_CLASSES:
        # ... and then try only the first 2 letters
        lang = lang[:2]
    if lang not in CONVERTER_CLASSES:
        raise NotImplementedError()
    if lang not in num2words_by_lang:
        return num2words(number, ordinal, lang, to, **kwargs)
    else:
        # Fixed implementation
        converter = globals()[num2words_by_lang[lang]]()
        if ordinal:
            return converter.to_ordinal(number)
        if to not in CONVERTES_TYPES:
            raise NotImplementedError()
        return getattr(converter, "to_{}".format(to))(number, **kwargs)
