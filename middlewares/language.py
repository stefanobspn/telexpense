from pathlib import Path

from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware

import database

I18N_DOMAIN = 'telexpense'
BASE_DIR = Path(__file__).parent.parent
LOCALES_DIR = BASE_DIR / 'locales'
SUPPORTED_LOCALES = {"en"}


class ACLMiddleware(I18nMiddleware):
    async def get_user_locale(self, action, args):
        user = types.User.get_current()

        # Getting current user language
        user_lang = database.get_user_lang(user.id)

        # If None, return english
        if user_lang in SUPPORTED_LOCALES:
            return user_lang

        return "en"


def setup_language(dp):
    i18n = ACLMiddleware(I18N_DOMAIN, LOCALES_DIR)
    dp.middleware.setup(i18n)
    return i18n
