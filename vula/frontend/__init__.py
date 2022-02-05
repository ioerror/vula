import pkg_resources

from .constants import _WIDTH, _HEIGHT
from .dataprovider import *

import gettext

locale_path = pkg_resources.resource_filename('vula', 'locale')
lang_translations = gettext.translation(
    domain="ui", localedir=locale_path, fallback=True
)
lang_translations.install()
