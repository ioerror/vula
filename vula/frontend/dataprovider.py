from typing import List, TypedDict

import pydbus
import yaml

from vula.common import escape_ansi
from vula.constants import _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH


class PeerType(TypedDict):
    name: str
    id: str
    other_names: str
    status: str
    endpoint: str
    allowed_ip: str
    latest_signature: str
    latest_handshake: str
    wg_pubkey: str


class StatusType(TypedDict):
    publish: str
    discover: str
    organize: str


class PrefsType(TypedDict):
    pin_new_peers: bool
    accept_nonlocal: bool
    auto_repair: bool
    subnets_allowed: list
    subnets_forbidden: list
    iface_prefix_allowed: list
    local_domains: list
    ephemeral_mode: bool
    accept_default_route: bool
    record_events: bool
    expire_time: int
    overwrite_unpinned: bool


class DataProvider:
    def get_peers(self) -> List[PeerType]:
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )

        # Get all peer ids from the dbus
        ids = organize.peer_ids("enabled")

        peers: List[PeerType] = []

        # Loop over all ids in the list
        for id in ids:
            # Create empty dict for peer
            peer_dict: PeerType = {
                "name": None,
                "id": None,
                "other_names": None,
                "status": None,
                "endpoint": None,
                "allowed_ip": None,
                "latest_signature": None,
                "latest_handshake": None,
                "wg_pubkey": None,
            }

            # Fill in the data
            peer_raw = organize.show_peer(id)
            peer_clear = escape_ansi(peer_raw)
            peer_lines = peer_clear.split("\n")

            peer_dict["name"] = peer_lines[0].lstrip().split(": ")[1]
            peer_dict["id"] = peer_lines[1].lstrip().split(": ")[1]
            if "other names" in peer_lines[2]:
                peer_dict["other_names"] = (
                    peer_lines[2].lstrip().split(": ")[1]
                )
                peer_dict["status"] = peer_lines[3].lstrip().split(": ")[1]
                peer_dict["endpoint"] = peer_lines[4].lstrip().split(": ")[1]
                peer_dict["allowed_ips"] = (
                    peer_lines[5].lstrip().split(": ")[1]
                )
                peer_dict["latest_signature"] = (
                    peer_lines[6].lstrip().split(": ")[1]
                )
                peer_dict["latest_handshake"] = (
                    peer_lines[7].lstrip().split(": ")[1]
                )
                peer_dict["wg_pubkey"] = peer_lines[8].lstrip().split(": ")[1]
            else:
                peer_dict["status"] = peer_lines[2].lstrip().split(": ")[1]
                peer_dict["endpoint"] = peer_lines[3].lstrip().split(": ")[1]
                peer_dict["allowed_ips"] = (
                    peer_lines[4].lstrip().split(": ")[1]
                )
                peer_dict["latest_signature"] = (
                    peer_lines[5].lstrip().split(": ")[1]
                )
                peer_dict["latest_handshake"] = (
                    peer_lines[6].lstrip().split(": ")[1]
                )
                peer_dict["wg_pubkey"] = peer_lines[7].lstrip().split(": ")[1]

            peers.append(peer_dict)

        return peers

    def get_prefs(self) -> PrefsType:
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )

        # Get the data from the organize dbus
        data = organize.show_prefs()
        items: PrefsType = yaml.safe_load(data)

        return items

    def get_status(self) -> StatusType:
        # Fetch the data from the systemd dbus
        systemd = pydbus.SystemBus().get(".systemd1")

        # Create an empty dict for the status
        status: StatusType = {
            "publish": None,
            "discover": None,
            "organize": None,
        }

        # Define names to consider in the result
        names = ["publish", "discover", "organize"]
        for name in names:
            # Template string for service name
            unit_name = "vula-%s.service" % (name,)
            try:
                unit = pydbus.SystemBus().get(
                    ".systemd1", systemd.GetUnit(unit_name)
                )
                status[name] = unit.ActiveState
            except Exception as ex:
                print(ex)
                return None

        return status

    def our_latest_descriptors(self):
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )
        return organize.our_latest_descriptors()

    def delete_peer(self, peer_vk):
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )
        organize.remove_peer(peer_vk)

    def rename_peer(self, peer_vk, name):
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )
        organize.set_peer(peer_vk, ["petname"], name)

    def pin_and_verify(self, peer_vk, peer_name):
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )
        organize.verify_and_pin_peer(peer_vk, peer_name)

    def add_peer(self, peer_vk, ip):
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )
        organize.peer_addr_add(peer_vk, ip)

    def set_pref(self, pref, value):
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )
        return organize.set_pref(pref, value)

    def add_pref(self, pref, value):
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )
        return organize.add_pref(pref, value)

    def remove_pref(self, pref, value):
        organize = pydbus.SystemBus().get(
            _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
        )
        organize.remove_pref(pref, value)
