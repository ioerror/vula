"""
vula constant values
"""

from typing import List
from ipaddress import ip_network

_LOG_FMT: str = "%(asctime)s: %(message)s"
_DATE_FMT: str = "%Y-%m-%d-%H:%M:%S"
_WG_INTERFACE: str = "vula"
_DUMMY_INTERFACE: str = "vula-net"

# this is registered for vula at https://ula.ungleich.ch/
_VULA_ULA_SUBNET: str = ip_network("fdff:ffff:ffdf::/48")

# Set an upper boundary of 1kB for the cache
_LRU_CACHE_MAX_SIZE: int = 1024

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
_DISCOVER_ALT_DBUS_NAME: str = "local.vula.discoveralt"
_PUBLISH_ALT_DBUS_NAME: str = "local.vula.publishalt"

# FIXME: these should not have the 1 in them, but pydbus publish() puts it
# there.  we should figure out how to make it work with the 1 removed from the
# object path (we want it in the interface name, but not the object path.)
_ORGANIZE_DBUS_PATH: str = "/local/vula/organize"
_DISCOVER_DBUS_PATH: str = "/local/vula/discover"
_PUBLISH_DBUS_PATH: str = "/local/vula/publish"
_DISCOVER_ALT_DBUS_PATH: str = "/local/vula/discoveralt"
_PUBLISH_ALT_DBUS_PATH: str = "/local/vula/publishalt"

_LINUX_MAIN_ROUTING_TABLE = 254

# from linux/include/uapi/linux/if_link.h
_IN6_ADDR_GEN_MODE_NONE = 1

_IPv4_GW_ROUTES = ('0.0.0.0/1', '128.0.0.0/1')
_IPv6_GW_ROUTES = ('::/1', '8000::/1')
_GW_ROUTES = _IPv4_GW_ROUTES + _IPv6_GW_ROUTES

_IPv4_LL = ip_network("169.254.0.0/16")
_IPv6_LL = ip_network("fe80::/10")
_IPv6_ULA = ip_network("fc00::/7")

# Update interval for the tray in seconds
_TRAY_UPDATE_INTERVAL = 5

# example descriptor for tests (use "vula verify my-descriptor" in
# testnet-shell to regenerate when something needs to change)
_TEST_DESC = "c=cBVKup6b9dM6hfY0pE81fCKPJ6EFVvT7m+Gkt/W7gIHhBl50fdKZzT5feHACzJXDRzhxYicoyi358tREqhcyWw==; dt=86400; e=0; hostname=vula-bookworm-test2.local.; pk=6T2K6Xcmlsr1XQVZTAHrZs/d9v3IadKYI+74559/3Aw=; port=5354; r=; s=PuDfyhWpftSbWUMMydt1Qv7o618KIli9ncxUkcPP8yqaspDXa0jJUnwNwydEpXjVfY96BmVu5Jwba8ahZPzBDA==; v4a=10.89.0.3; v6a=fdff:ffff:ffdf:e436:dfba:4f29:bcbf:6af8,fe80::cc69:7dff:fe6b:9e79,fd54:f27a:17c1:3a61::3; vf=1743985213; vk=Gy+arU0cowJC2vek9EnoGHVSQxUl5Qv1LUrDL/WjGos=;"  # noqa: E501

# second test descriptor, where signature doesn't need to verify. this gets
# updated manually, because tests refer to its specific values which so we want
# them to remain stable (and they are randomly generated when generating a new
# signed version of the first _TEST_DESC above).
_TEST_DESC_UNSIGNED = "c=NnoGEZ4W+d6TE22+Qyau0LF513FM43EagOP9aiSX9KhTCS1Gryt7qDoM04j7p0KQRJxwkcPEO/MpIJE5/bJKYQ==; dt=86400; e=0; hostname=vula-bookworm-test1.local.; p=fdff::1; pk=3w5/xje5jsdUCX30JfS/L/bMuwZRniK69dAVprN7t3c=; port=5354; r=; v4a=10.89.0.2; v6a=fdff:ffff:ffdf:989f:24cf:bda:1262:cfc6,fe80::bc92:4dff:fe82:30d,fd54:f27a:17c1:3a61::2; vf=1743974365; vk=afToKyN29ubu4DkhUMLoGIt5WjbsgEHYuccNtxvbjmA=;"  # noqa: E501
