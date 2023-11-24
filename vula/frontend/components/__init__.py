import gettext

import pkg_resources

from .qr_code_label import QRCodeLabel

locale_path = pkg_resources.resource_filename('vula', 'locale')
lang_translations = gettext.translation(
    domain="ui.components", localedir=locale_path, fallback=True
)
lang_translations.install()
