"""
vula constant values
"""
from typing import List


_LOG_FMT: str = "%(asctime)s: %(message)s"
_DATE_FMT: str = "%Y-%m-%d-%H:%M:%S"
_WG_INTERFACE: str = "vula"

_WG_SERVICES: List = [
    "vula-publish.service",
    "vula-organize.service",
    "vula-discover.service",
    "vula.slice",
]
_ORGANIZE_CACHE_BASEDIR: str = "/var/lib/vula-organize/"
_WG_PORT: int = 5354
_TABLE: int = 666
_FWMARK: int = 555
_IP_RULE_PRIORITY: int = 666
_SERVICE: str = "_opabinia._udp"
_DOMAIN: str = ".local."
_LABEL: str = "_opabinia._udp.local."
_DEFAULT_INTERFACE: str = _WG_INTERFACE
_B64ALPHABET: str = (
    "1234567890=/+abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
)
_ORGANIZE_CACHE_FILE: str = _ORGANIZE_CACHE_BASEDIR + "vula-organize-cache"
_ORGANIZE_CONF_FILE: str = _ORGANIZE_CACHE_BASEDIR + "vula-organize.yaml"
_ORGANIZE_KEYS_CONF_FILE: str = _ORGANIZE_CACHE_BASEDIR + "keys.yaml"
_ORGANIZE_HOSTS_FILE: str = _ORGANIZE_CACHE_BASEDIR + "hosts"
_ORGANIZE_UPDATE_TEMP: str = "vula-organize-peer-update-"
_DEFAULT_TABLE: int = 666

_ORGANIZE_DBUS_NAME: str = "local.vula.organize"
_DISCOVER_DBUS_NAME: str = "local.vula.discover"
_PUBLISH_DBUS_NAME: str = "local.vula.publish"

# FIXME: these should not have the 1 in them, but pydbus publish() puts it there.
#       we should figure out how to make it work with the 1 removed from the
#       object path (we want it in the interface name, but not the object
#       path.)
_ORGANIZE_DBUS_PATH: str = "/local/vula/organize"
_DISCOVER_DBUS_PATH: str = "/local/vula/discover"
_PUBLISH_DBUS_PATH: str = "/local/vula/publish"

_LINUX_MAIN_ROUTING_TABLE = 254

IPv4_GW_ROUTES = ('0.0.0.0/1', '128.0.0.0/1')
