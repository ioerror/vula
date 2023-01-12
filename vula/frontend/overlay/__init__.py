import pkg_resources

from .peer_details_overlay import PeerDetailsOverlay
from .descriptor_overlay import DescriptorOverlay
from .verification_key_overlay import VerificationKeyOverlay
from .help_overlay import HelpOverlay
from .popupMessage import PopupMessage

import gettext

locale_path = pkg_resources.resource_filename('vula', 'locale')
lang_translations = gettext.translation(
    domain="ui.overlay", localedir=locale_path, fallback=True
)
lang_translations.install()
