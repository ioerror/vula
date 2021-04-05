"""
vula constant values
"""
from typing import List


_LOG_FMT: str = "%(asctime)s: %(message)s"
_DATE_FMT: str = "%Y-%m-%d-%H:%M:%S"
_WG_INTERFACE: str = "vula"
_VULA_TEMPLATE: str = """[Interface]
ListenPort = {a}
PrivateKey = {b}
Table = {c}
FwMark = {d}
PostUp = ip -4 rule add not fwmark {d} table {c} pref 666;ip -6 rule add not fwmark {d} table {c} pref 666;
PostDown = ip -4 rule delete table {c};ip -6 rule delete table {c};
"""

_VULA_TEMPLATE = _VULA_TEMPLATE.format(a={0}, b={1}, c={2}, d={3})
_WG_QUICK_SERVICE: str = "wg-quick@" + _WG_INTERFACE + ".service"
_WG_SERVICES: List = [
    "vula-publish.service",
    "vula-organize.service",
    "vula-discover.service",
    "vula-petname.service",
    "vula.slice",
]
_ORGANIZE_CACHE_BASEDIR: str = "/var/lib/vula-organize/"
_WG_CONFIG_FILE: str = "/etc/wireguard/" + _WG_INTERFACE + ".conf"
_WG_PRIVATE_KEY_FILE: str = "/etc/wireguard/" + _WG_INTERFACE + ".priv"
_WG_PUBLIC_KEY_FILE: str = "/etc/wireguard/" + _WG_INTERFACE + ".pub"
_ED25519_SEED_FILE: str = "/etc/wireguard/" + _WG_INTERFACE + ".seed"
_CSIDH_PRIVATE_KEY_FILE: str = _ORGANIZE_CACHE_BASEDIR + "csidh-" + _WG_INTERFACE + ".priv"
_CSIDH_PUBLIC_KEY_FILE: str = "/etc/wireguard/" + "csidh-" + _WG_INTERFACE + ".pub"
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

_PETNAME_ORGANIZE_HOSTSFILE: str = "/var/lib/vula-organize/vula-organize-hosts"
_PETNAME_HOSTSFILE_BASEDIR: str = "/var/lib/vula-petname/"
_PETNAME_HOSTSFILE: str = _PETNAME_HOSTSFILE_BASEDIR + "hosts"
_PETNAME_HOSTSFILE_MODE: int = 755
_PETNAME_SOCKET: str = "/var/lib/private/vula-organize/hosts"
_PETNAME_SOCKET_MODE: int = 660

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
