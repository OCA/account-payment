# pylint: disable=missing-import-error
from num2words import CONVERTER_CLASSES, CONVERTES_TYPES, num2words
from num2words.lang_ES import Num2Word_ES

num2words_by_lang = {"es": "Num2WordESCustom"}


class Num2WordESCustom(Num2Word_ES):
    # Replace centavo to céntimo. Original method copy
    def to_currency(self, val, longval=True, old=False):
        hightxt, lowtxt = "euro/s", u"céntimo/s"
        if old:
            hightxt, lowtxt = "peso/s", "peseta/s"
        result = self.to_splitnum(
            val, hightxt=hightxt, lowtxt=lowtxt, divisor=1, jointxt="y", longval=longval
        )
        # Handle exception, in spanish is "un euro" and not "uno euro"
        return result.replace("uno", "un")


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
