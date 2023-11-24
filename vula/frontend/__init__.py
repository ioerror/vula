import gettext

import pkg_resources

from .constants import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_CARD,
    BACKGROUND_COLOR_ENTRY,
    BACKGROUND_COLOR_ERROR,
    FONT,
    FONT_SIZE_HEADER,
    FONT_SIZE_HEADER_2,
    FONT_SIZE_TEXT_L,
    FONT_SIZE_TEXT_M,
    FONT_SIZE_TEXT_S,
    FONT_SIZE_TEXT_XL,
    FONT_SIZE_TEXT_XS,
    FONT_SIZE_TEXT_XXL,
    HEIGHT,
    IMAGE_BASE_PATH,
    TEXT_COLOR_BLACK,
    TEXT_COLOR_GREEN,
    TEXT_COLOR_GREY,
    TEXT_COLOR_HEADER,
    TEXT_COLOR_HEADER_2,
    TEXT_COLOR_ORANGE,
    TEXT_COLOR_PURPLE,
    TEXT_COLOR_RED,
    TEXT_COLOR_WHITE,
    TEXT_COLOR_YELLOW,
    WIDTH,
)
from .dataprovider import DataProvider, PeerType, PrefsType, StatusType

locale_path = pkg_resources.resource_filename('vula', 'locale')
lang_translations = gettext.translation(
    domain="ui", localedir=locale_path, fallback=True
)
lang_translations.install()
