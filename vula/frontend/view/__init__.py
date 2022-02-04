import pkg_resources

from .peers import *
from .prefs import *
from .qr_code_label import *
from .information import *

import gettext

locale_path = pkg_resources.resource_filename('vula', 'locale')
lang_translations = gettext.translation(
    domain="ui.view", localedir=locale_path, fallback=True
)
lang_translations.install()
