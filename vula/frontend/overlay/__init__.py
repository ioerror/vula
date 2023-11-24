import gettext

import pkg_resources

from .descriptor_overlay import DescriptorOverlay
from .help_overlay import HelpOverlay
from .peer_details_overlay import PeerDetailsOverlay
from .popupMessage import PopupMessage
from .verification_key_overlay import VerificationKeyOverlay

locale_path = pkg_resources.resource_filename('vula', 'locale')
lang_translations = gettext.translation(
    domain="ui.overlay", localedir=locale_path, fallback=True
)
lang_translations.install()
