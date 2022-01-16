import re

import pydbus
import yaml

from vula.constants import _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH


class DataProvider:
    def get_peers(self):
        bus = pydbus.SystemBus()
        organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)

        def escape_ansi(line):
            ansi_escape = re.compile(
                r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]'
            )
            return ansi_escape.sub('', line)

        # Get all peer ids from the dbus
        ids = organize.peer_ids('enabled')

        peers = []

        # Loop over all ids in the list
        for id in ids:
            # Create empty dict for peer
            peer_dict = {
                'name': None,
                'id': None,
                'other_names': None,
                'status': None,
                'endpoint': None,
                'allowed_ip': None,
                'latest_signature': None,
                'latest_handshake': None,
                'wg_pubkey': None,
            }

            # Fill in the data
            peer_raw = organize.show_peer(id)
            peer_clear = escape_ansi(peer_raw)
            peer_lines = peer_clear.split("\n")

            peer_dict['name'] = peer_lines[0].lstrip().split(": ")[1]
            peer_dict['id'] = peer_lines[1].lstrip().split(": ")[1]
            if 'other names' in peer_lines[2]:
                peer_dict['other_names'] = (
                    peer_lines[2].lstrip().split(": ")[1]
                )
                peer_dict['status'] = peer_lines[3].lstrip().split(": ")[1]
                peer_dict['endpoint'] = peer_lines[4].lstrip().split(": ")[1]
                peer_dict['allowed_ips'] = (
                    peer_lines[5].lstrip().split(": ")[1]
                )
                peer_dict['latest_signature'] = (
                    peer_lines[6].lstrip().split(": ")[1]
                )
                peer_dict['latest_handshake'] = (
                    peer_lines[7].lstrip().split(": ")[1]
                )
                peer_dict['wg_pubkey'] = peer_lines[8].lstrip().split(": ")[1]
            else:
                peer_dict['status'] = peer_lines[2].lstrip().split(": ")[1]
                peer_dict['endpoint'] = peer_lines[3].lstrip().split(": ")[1]
                peer_dict['allowed_ips'] = (
                    peer_lines[4].lstrip().split(": ")[1]
                )
                peer_dict['latest_signature'] = (
                    peer_lines[5].lstrip().split(": ")[1]
                )
                peer_dict['latest_handshake'] = (
                    peer_lines[6].lstrip().split(": ")[1]
                )
                peer_dict['wg_pubkey'] = peer_lines[7].lstrip().split(": ")[1]

            peers.append(peer_dict)

        return peers

    def get_prefs(self):
        bus = pydbus.SystemBus()
        organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)

        # Get the data from the organize dbus
        data = organize.show_prefs()
        items = yaml.safe_load(data)

        return items

    def get_status(self):
        bus = pydbus.SystemBus()

        # Fetch the data from the systemd dbus
        systemd = bus.get('.systemd1')

        # Create an empty dict for the status
        status = {'publish': None, 'discover': None, 'organize': None}

        # Define names to consider in the result
        names = ['publish', 'discover', 'organize']
        for name in names:
            # Template string for service name
            unit_name = "vula-%s.service" % (name,)
            try:
                unit = bus.get('.systemd1', systemd.GetUnit(unit_name))
                status[name] = unit.ActiveState
            except Exception as ex:
                print(ex)
                return None

        return status

    def our_latest_descriptors(self):
        bus = pydbus.SystemBus()
        organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)
        return organize.our_latest_descriptors()

    def delete_peer(self, peer_vk):
        bus = pydbus.SystemBus()
        organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)
        organize.remove_peer(peer_vk)

    def rename_peer(self, peer_vk, name):
        bus = pydbus.SystemBus()
        organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)
        organize.set_peer(peer_vk, ["petname"], name)

    def pin_and_verify(self, peer_vk, peer_name):
        bus = pydbus.SystemBus()
        organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)
        organize.verify_and_pin_peer(peer_vk, peer_name)

    def add_peer(self, peer_vk, ip):
        bus = pydbus.SystemBus()
        organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)
        organize.peer_addr_add(peer_vk, ip)
