import gettext

import pkg_resources

from .peers import Peers
from .prefs import Prefs

locale_path = pkg_resources.resource_filename('vula', 'locale')
lang_translations = gettext.translation(
    domain="ui.view", localedir=locale_path, fallback=True
)
lang_translations.install()
