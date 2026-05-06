import i18n

i18n.load_path.append("locales")
i18n.set("locale", "en")


class Translation:
    _locale: str = "pl"

    def __init__(self, locale: str) -> None:
        self._locale = locale

    def __call__(self, key: str, **kwargs):
        return i18n.t(key, locale=self._locale, **kwargs)
