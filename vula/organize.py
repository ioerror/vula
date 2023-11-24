"""
 *vula-organize* is a daemon that reads configuration files as well as peer
 descriptors. It configures the `vula` WireGuard device for new peers. It
 requires administrative privileges for managing the `vula` device and for
 modifying routing information. It does not need network access.

"""
from __future__ import annotations

import os
import pdb
import time
from ipaddress import ip_address, ip_network
from logging import Logger, getLogger
from pathlib import Path
from platform import node

import click
import pydbus
from gi.repository import GLib
from schema import And
from schema import Optional as Optional_
from schema import Schema, Use

from .common import (
    addrs_in_subnets,
    attrdict,
    b64_bytes,
    chown_like_dir_if_root,
    jsonrepr,
    memoize,
    raw,
    schemattrdict,
    yamlrepr,
    yamlrepr_hl,
)
from .configure import Configure
from .constants import (
    _DEFAULT_INTERFACE,
    _DEFAULT_TABLE,
    _DISCOVER_DBUS_NAME,
    _DISCOVER_DBUS_PATH,
    _DOMAIN,
    _FWMARK,
    _IP_RULE_PRIORITY,
    _ORGANIZE_CONF_FILE,
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_HOSTS_FILE,
    _ORGANIZE_KEYS_CONF_FILE,
    _PUBLISH_DBUS_NAME,
    _PUBLISH_DBUS_PATH,
    _WG_PORT,
    IPv4_GW_ROUTES,
)
from .csidh import ctidh, ctidh_parameters, hkdf
from .discover import Discover
from .engine import Engine, Result
from .notclick import DualUse
from .peer import Descriptor, PeerCommands, Peers
from .prefs import Prefs, PrefsCommands
from .publish import Publish
from .sys import Sys


class SystemState(schemattrdict):

    """
    The SystemState object stores the parts of the system's state which are
    relevant to events in the organize state engine. The object should be
    updated (replaced) whenever these values change, via the
    event_NEW_SYSTEM_STATE event.
    """

    schema = Schema(
        dict(
            current_subnets={Optional_(Use(ip_network)): [Use(ip_address)]},
            our_wg_pk=b64_bytes.with_len(32),
            gateways=[Use(ip_address)],
        )
    )

    default = dict(
        our_wg_pk=b'\x00' * 32,
        current_subnets={},
        gateways=[],
    )

    @classmethod
    def read(cls, organize):
        subnets, gateways = organize.sys._get_system_state()
        return cls(
            gateways=gateways,
            current_subnets=subnets,
            our_wg_pk=organize.our_wg_pk,
        )

    @property
    def current_ips(self):
        """
        Currently assigned IP addresses of the system.

        >>> SystemState().current_ips
        []
        >>> SystemState(current_subnets={'10.0.0.0/24': ['10.0.0.1',
        ... '10.0.0.2']}).current_ips
        [IPv4Address('10.0.0.1'), IPv4Address('10.0.0.2')]
        >>> SystemState(current_subnets={'10.0.0.0/24': ['10.0.0.1'],
        ... '192.168.0.0/24': ['192.168.1.1']}).current_ips
        [IPv4Address('10.0.0.1'), IPv4Address('192.168.1.1')]
        >>> SystemState(current_subnets={'FE80::/10': ['FE80::FFFF:FFFE',
        ... 'FE80::FFFF:FFFD']}).current_ips
        [IPv6Address('fe80::ffff:fffe'), IPv6Address('fe80::ffff:fffd')]
        >>> SystemState(current_subnets={'FE80::/10': ['FE80::FFFF:FFFE'],
        ... 'FC00::/7': ['FC00::FFFF:FFFE']}).current_ips
        [IPv6Address('fe80::ffff:fffe'), IPv6Address('fc00::ffff:fffe')]
        """
        return [
            ip for subnet in self.current_subnets.values() for ip in subnet
        ]


class OrganizeState(Engine, yamlrepr_hl):

    schema = Schema(
        And(
            Use(dict),
            {
                'prefs': Use(Prefs),
                'peers': Use(Peers),
                'system_state': Use(SystemState),
                'event_log': object,
            },
            And(
                lambda state: not state['peers'].conflicts,
                error="conflicting peers: {[peers].conflicts}",
            ),
        )
    )

    default = dict(
        prefs=Prefs.default, system_state={}, peers={}, event_log=[]
    )

    restricted = [
        "peers.*.descriptor"
    ]  # FIXME: implement filter for 1-op direct events?

    def _check_freshness(self, descriptor):
        # FIXME: check dt and vf here
        return True

    def record(self, res):
        if self.prefs.record_events:
            self.event_log.append(raw(res))

    @Engine.event
    def event_VERIFY_AND_PIN_PEER(self, vk, hostname):
        _id = self.peers.with_hostname(hostname).id
        if vk == _id:
            self.action_EDIT('SET', ['peers', vk, 'verified'], True)
            self.action_EDIT('SET', ['peers', vk, 'pinned'], True)
        else:
            raise Exception(f"Expected {hostname}: expected: {vk} have: {_id}")

    @Engine.event
    def event_USER_REMOVE_PEER(self, query):
        peer = self.peers.query(query)
        if peer:
            self.action_REMOVE_PEER(peer)
        else:
            self.action_IGNORE("no such peer")

    @Engine.event
    def event_USER_PEER_ADDR_ADD(self, vk, ip):
        "user added IP address"
        peer = self.peers.get(vk)
        if peer:
            self.action_PEER_ADDR_ADD(peer, vk, ip)
        else:
            self.action_IGNORE("no such peer")

    @Engine.action
    def action_PEER_ADDR_ADD(self, peer, vk, ip):
        "added IP address"
        ipa = ip_address(ip)
        self._SET(('peers', vk, 'IPv%saddrs' % (ipa.version,), ip), True)
        self.result.add_triggers(sync_peer=(peer.id,))

    @Engine.event
    def event_USER_PEER_ADDR_DEL(self, vk, ip):
        "user removed IP address"
        peer = self.peers.get(vk)
        if peer:
            self.action_PEER_ADDR_DEL(peer, vk, ip)
        else:
            self.action_IGNORE("no such peer")

    @Engine.action
    def action_PEER_ADDR_DEL(self, peer, vk, ip):
        "removed IP address"
        ipa = ip_address(ip)
        self._REMOVE(('peers', vk, 'IPv%saddrs' % (ipa.version,)), ip)
        self.result.add_triggers(sync_peer=(peer.id,))
        self.result.add_triggers(
            remove_routes=(ip + ('/32' if ipa.version == 4 else '/128'),)
        )

    @Engine.event
    def event_USER_EDIT(self, operation, path, value):
        self.action_EDIT(operation, path, value)

    @Engine.event
    def event_RELEASE_GATEWAY(self):
        cur_gw = list(self.peers.limit(use_as_gateway=True).values())
        if cur_gw:
            self.action_EDIT(
                'SET', ['peers', cur_gw[0].id, 'use_as_gateway'], False
            )
            self.result.add_triggers(get_new_system_state=())
        else:
            self.action_IGNORE("no current gateway peer")

    @Engine.action
    def action_EDIT(self, operation, path, value):
        getattr(self, '_' + operation)(path, value)
        if path[0] == 'peers':
            # bug: this doesn't work for the REMOVE operation where there is no
            # path[1] but the peer remove command calls event_USER_REMOVE_PEER
            # so that is ok for now
            self.result.add_triggers(sync_peer=(path[1],))
        elif path[0] == 'prefs':
            self.result.add_triggers(get_new_system_state=())
        # FIXME: with more granular actions for peers and prefs, we could
        # remove this call remove_unknown trigger. but for now, it is still
        # necessary.
        self.result.add_triggers(remove_unknown=())

    @Engine.event
    def event_NEW_SYSTEM_STATE(self, new_system_state):
        self.action_ADJUST_TO_NEW_SYSTEM_STATE(new_system_state)

    @Engine.action
    def action_ADJUST_TO_NEW_SYSTEM_STATE(self, new_system_state):
        # IPv6 analysis: not ipv6 ready
        # Please enhance this function to support ipv6
        cur_gw = list(self.peers.limit(use_as_gateway=True).values())
        cur_gw = cur_gw and cur_gw[0]
        if (
            cur_gw
            and (not cur_gw.pinned)
            and (
                not (set(cur_gw.enabled_ips) & set(new_system_state.gateways))
            )
        ):
            # if a non-pinned peer had our gateway IP but no longer does,
            # remove its gateway flag
            self._SET(('peers', cur_gw.id, 'use_as_gateway'), False)
            self.result.add_triggers(remove_routes=(IPv4_GW_ROUTES,))
        if not (cur_gw and cur_gw.pinned):
            # if there isn't a pinned peer acting as the gateway.
            # FIXME: this could set two peers as the gateway if the system has
            # multiple default routes! we need to think about how to handle
            # that...
            for gateway in new_system_state.gateways:
                hit = self.peers.by('enabled_ips').get(gateway)
                if hit:
                    self._SET(('peers', hit[0].id, 'use_as_gateway'), True)
                    self.result.add_triggers(sync_peer=(hit[0].id,))
                    # first hit wins (there could be multiples if we have
                    # multiple default routes, but only one can get
                    # allowedips=/0 so we just take the first one.)
                    break
        for peer in self.peers.limit(pinned=False).values():
            if not addrs_in_subnets(
                peer.enabled_ips, new_system_state.current_subnets
            ):
                # remove unpinned peers that are no longer local
                self.action_REMOVE_PEER(peer)
        self._SET('system_state', new_system_state)

        # TODO:
        # remove endpoints from pinned peers that became non-local

    @Engine.event
    def event_INCOMING_DESCRIPTOR(self, descriptor):

        if str(descriptor.pk) == str(self.system_state.our_wg_pk):
            return self.action_IGNORE(descriptor, "has our wg pk")

        existing_peer = self.peers.get(descriptor.id)

        if not self._check_freshness(descriptor):
            return self.action_REJECT(descriptor, "timestamp too old")

        if existing_peer and descriptor.vf <= existing_peer.descriptor.vf:
            return self.action_IGNORE(descriptor, "replay")

        if not addrs_in_subnets(
            descriptor.addrs, self.system_state.current_subnets
        ):
            return self.action_REJECT(
                descriptor,
                "wrong subnet, current subnets are %r"
                % (self.system_state.current_subnets,),
            )

        if not any(
            descriptor.hostname.endswith(domain)
            for domain in self.prefs.local_domains
        ):
            return self.action_REJECT(descriptor, "invalid domain")

        conflicting_peers = self.peers.conflicts_for_descriptor(descriptor)

        if conflicting_peers:

            for conflicting_peer in conflicting_peers:
                if conflicting_peer.pinned:
                    return self.action_REJECT(
                        descriptor, ("conflict", conflicting_peer)
                    )

            for conflicting_peer in conflicting_peers:
                self.action_REMOVE_PEER(conflicting_peer)

        if existing_peer:
            self.action_UPDATE_PEER_DESCRIPTOR(existing_peer, descriptor)
        else:
            self.action_ACCEPT_NEW_PEER(descriptor)

    @Engine.action
    def action_ACCEPT_NEW_PEER(self, descriptor):
        peer = descriptor.make_peer(
            pinned=False
            if descriptor.ephemeral
            else bool(self.prefs.pin_new_peers)
        )
        self._SET(('peers', descriptor.id), peer)
        if set(descriptor.addrs) & set(self.system_state.gateways):
            # BUG: this will fail (new peer won't be accepted) if the new peer
            # has a gateway IP and there is already another gateway. it fails
            # closed, but should perhaps do so more gracefully? this could only
            # happen if (1) the existing gateway is pinned or, if (2) there are
            # multiple default routes (because otherwise the other gateway
            # would've already been removed before action_ACCEPT_NEW_PEER was
            # called).
            self._SET(('peers', descriptor.id, 'use_as_gateway'), True)
        self.result.add_triggers(sync_peer=(peer.id,))

    @Engine.action
    def action_UPDATE_PEER_DESCRIPTOR(self, peer, desc):
        self._SET(('peers', peer.id, 'descriptor'), desc)
        self._ADD(
            ('peers', peer.id, 'IPv4addrs'),
            {i: True for i in desc.IPv4addrs if i not in peer.IPv4addrs},
        )
        self._ADD(
            ('peers', peer.id, 'IPv6addrs'),
            {i: True for i in desc.IPv6addrs if i not in peer.IPv6addrs},
        )
        if desc.hostname not in peer.nicknames:
            self._SET(('peers', peer.id, 'nicknames', desc.hostname), True)

        if set(desc.addrs) & set(self.system_state.gateways):
            self._SET(('peers', desc.id, 'use_as_gateway'), True)

        self.result.add_triggers(sync_peer=(peer.id,))

    @Engine.action
    def action_REMOVE_PEER(self, peer):
        # IPv6 analysis: not ipv6 ready.
        # Please enhance this function to support ipv6
        self._REMOVE('peers', peer.id)
        self.result.add_triggers(
            remove_wg_peer=(str(peer.wg_pk),),
            remove_routes=(tuple(map(str, peer.routes)),),
        )
        if peer.use_as_gateway:
            # FIXME: this doesn't specify the routing table. maybe need to make
            # triggers api accept kwargs too?
            self.result.add_triggers(remove_routes=(IPv4_GW_ROUTES,))
            # these routes are currently only removed because we still call
            # sync (aka full repair) on system state change

    @Engine.action
    def action_REJECT(self, descriptor, reason):
        pass

    @Engine.action
    def action_IGNORE(self, *a):
        # same as reject, different for logging
        pass

    @Engine.action
    def action_LOG(self, message, *args):
        pass  # the decorator actually does the logging


@DualUse.object(
    short_help="Maintain routes and wg peer configurations",
    invoke_without_command=True,
)
@click.option(
    "-t",
    "--table",
    type=int,
    show_default=True,
    default=_DEFAULT_TABLE,
    help="Which routing table to use",
)
@click.option(
    "-i",
    "--interface",
    show_default=True,
    default=_DEFAULT_INTERFACE,
    help='WireGuard interface name',
)
@click.option(
    "-c",
    "--state-file",
    default=_ORGANIZE_CONF_FILE,
    show_default=True,
    help="YAML state file",
)
@click.option(
    "-k",
    "--keys-file",
    default=_ORGANIZE_KEYS_CONF_FILE,
    show_default=True,
    help="YAML configuration file for cryptographic keys",
)
@click.option(
    "-p",
    "--port",
    default=_WG_PORT,
    show_default=True,
    help="path to base directory for organize state",
)
@click.option(
    "-m",
    "--fwmark",
    default=_FWMARK,
    show_default=True,
    help="path to base directory for organize state",
)
@click.option(
    "-r",
    "--ip-rule-priority",
    default=_IP_RULE_PRIORITY,
    show_default=True,
    help="path to base directory for organize state",
)
@click.pass_context
class Organize(attrdict):
    """
    vula's organize daemon processes events such as new descriptors or system
    configuration changes, and maintains the configuration of the wireguard
    interface and routing table.

    It provides dbus interfaces for client tools to view and modify its state.
    """

    dbus = '''
    <node>
      <interface name='local.vula.organize1.Sync'>
        <method name='sync'>
          <arg type='b' name='dry_run' direction='in'/>
          <arg type='as' name='response' direction='out'/>
        </method>
      </interface>
      <interface name='local.vula.organize1.Debug'>
        <method name='dump_state'>
          <arg type='s' name='response' direction='out'/>
          <arg type='b' name='interactive' direction='in'/>
        </method>
        <method name='test_auth'>
            <arg type='b' name='interactive' direction='in'/>
            <arg type='s' name='response' direction='out'/>
        </method>
      </interface>
      <interface name='local.vula.organize1.Peers'>
        <method name='show_peer'>
          <arg type='s' name='query' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='peer_descriptor'>
          <arg type='s' name='query' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='peer_ids'>
          <arg type='s' name='which' direction='in'/>
          <arg type='as' name='response' direction='out'/>
        </method>
        <method name='rediscover'>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='set_peer'>
          <arg type='s' name='vk' direction='in'/>
          <arg type='as' name='path' direction='in'/>
          <arg type='s' name='value' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='remove_peer'>
          <arg type='s' name='vk' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='peer_addr_add'>
          <arg type='s' name='vk' direction='in'/>
          <arg type='s' name='value' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='peer_addr_del'>
          <arg type='s' name='vk' direction='in'/>
          <arg type='s' name='value' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='our_latest_descriptors'>
          <arg type='s' name='descriptors' direction='out'/>
        </method>
        <method name='get_vk_by_name'>
          <arg type='s' name='hostname' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='verify_and_pin_peer'>
          <arg type='s' name='vk' direction='in'/>
          <arg type='s' name='hostname' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
      </interface>
      <interface name='local.vula.organize1.ProcessDescriptor'>
        <method name='process_descriptor_string'>
          <arg type='s' name='descriptor' direction='in'/>
          <arg type='s' name='response' direction='out'/>
        </method>
      </interface>
      <interface name='local.vula.organize1.Prefs'>
        <method name='show_prefs'>
          <arg type='s' name='response' direction='out'/>
        </method>
        <method name='set_pref'>
          <arg type='s' name='response' direction='out'/>
          <arg type='s' name='pref' direction='in'/>
          <arg type='s' name='value' direction='in'/>
        </method>
        <method name='add_pref'>
          <arg type='s' name='response' direction='out'/>
          <arg type='s' name='pref' direction='in'/>
          <arg type='s' name='value' direction='in'/>
        </method>
        <method name='remove_pref'>
          <arg type='s' name='response' direction='out'/>
          <arg type='s' name='pref' direction='in'/>
          <arg type='s' name='value' direction='in'/>
        </method>
        <method name='release_gateway'>
          <arg type='s' name='response' direction='out'/>
        </method>
      </interface>
    </node>
    '''

    def __init__(self, ctx, **kw):
        self.update(**kw)
        self.log: Logger = getLogger()
        self.log.debug("Debug level logging enabled")
        self._configure = Configure(keys_conf_file=self.keys_file)
        self._ctidh_dh = None
        self._keys = self._configure.generate_or_read_keys()
        self.sys = Sys(self)
        self._state: OrganizeState = self._load_state()
        self._state.trigger_target = self.sys
        self._state.save = self.save
        self._state.debug_log = self.log.debug
        self._latest_descriptors = {}

        if ctx.invoked_subcommand is None:
            self.run(monolithic=False)

    def ctidh_dh(self, pk):
        if self._ctidh_dh is None:
            self.log.debug("Initializing CTIDH")
            _ctidh = ctidh(ctidh_parameters)
            sk = bytes(self._keys.pq_ctidhP512_sec_key)

            @memoize
            def _ctidh_dh(pk: bytes):
                self.log.debug("Generating CTIDH PSK for pk {}".format(pk))
                return _ctidh.dh(
                    _ctidh.private_key_from_bytes(sk),
                    _ctidh.public_key_from_bytes(pk),
                )

            self._ctidh_dh = _ctidh_dh
        raw_key = self._ctidh_dh(bytes(pk))
        # XXX To ensure that even if CTIDH is broken, we should integrate a DH
        # from a Curve-448 using a hybrid construction that is as secure as the
        # most secure of either (ctidh, curve448)
        psk = hkdf(raw_key)
        return psk

    @property
    def our_wg_pk(self):
        return str(self._keys.wg_Curve25519_pub_key)

    def our_latest_descriptors(self):
        return repr(jsonrepr(self._latest_descriptors))

    def _construct_service_descriptor(
        self, ip_addrs: str, vf: int
    ) -> Descriptor:
        self.log.info("Constructing service descriptor id: %s", vf)
        # XXX add Curve448 pk for hybrid DH
        return Descriptor(
            {
                "pk": self._keys.wg_Curve25519_pub_key,
                "c": self._keys.pq_ctidhP512_pub_key,
                "addrs": ip_addrs,
                "vk": self._keys.vk_Ed25519_pub_key,
                "vf": vf,
                "dt": "86400",
                "port": str(self.port),
                "hostname": node() + _DOMAIN,
                "r": '',
                "e": False,
            }
        ).sign(self._keys.vk_Ed25519_sec_key)

    @DualUse.method()
    def get_new_system_state(self):
        old_state = self.state.system_state.copy()
        new_system_state = SystemState.read(self)
        res = self.state.event_NEW_SYSTEM_STATE(new_system_state)
        if res.error:
            click.exit("Fatal unable to handle new system state: %r" % (res,))
        if old_state == new_system_state:
            self.log.info("system state unchanged")
        else:
            # FIXME: ensure that triggers do everything necessary, and then
            # remove this full repair sync call here:
            self.sync()
            self._instruct_zeroconf()
        return res

    def _load_state(self):
        """
        Deserializes the state object from disk and returns it
        """
        self.log.debug("Loading state file")
        try:
            state = OrganizeState.from_yaml_file(self.state_file)
            self.log.debug("Loaded state with %s peers" % (len(state.peers),))
        except Exception as ex:
            self.log.info("Couldn't load state file: %r", ex)

            state = OrganizeState()

            if os.path.exists(self.state_file):
                self.log.info(
                    "Existing state file will be overwritten because it was "
                    "malformed: %r",
                    ex
                    # XXX we should probably move the malformed file aside here
                )
            self.log.debug("Created new OrganizeState")

        if state.event_log:
            self.log.info(
                "event_log contains %s entries" % (len(state.event_log),)
            )
        return state

    @property
    def state(self):
        return self._state

    @property
    def peers(self):
        return self._state.peers

    @property
    def prefs(self):
        return self._state.prefs

    @DualUse.method()
    def _write_hosts_file(self):
        """
        Write the hosts file
        """
        hosts_file: str = _ORGANIZE_HOSTS_FILE
        hosts = {
            name: list(peer.descriptor.addrs)[0]
            # XXX make this use the "best ip" logic
            for peer in self.peers.limit(enabled=True).values()
            for name in peer.enabled_names
        }
        Path(hosts_file).touch(mode=0o644)
        with click.open_file(
            hosts_file, mode='w', encoding='utf-8', atomic=True
        ) as fh:
            fh.write(
                "\n".join("%s %s" % (ip, host) for host, ip in hosts.items())
                + "\n"
            )
        chown_like_dir_if_root(hosts_file)
        return True

    @DualUse.method()
    def save(self):
        """
        Save state to disk

        (should be no-op if run from commandline in a new organize instance)
        """
        self.state.write_yaml_file(self.state_file, mode=0o600, autochown=True)
        self.log.info("vula state file updated: %i peers", len(self.peers))
        self._write_hosts_file()

    @DualUse.method()
    def verify_and_pin_peer(self, vk, hostname):
        return str(
            yamlrepr(raw(self.state.event_VERIFY_AND_PIN_PEER(vk, hostname)))
        )

    @DualUse.method(
        opts=(
            click.option('-n', '--dryrun', is_flag=True),
            click.option('-v', '--verbose', is_flag=True),
        )
    )
    def sync(self, dryrun=False, verbose=False, firstrun=False):
        """
        Sync system to the desired organized state
        """
        res = []
        res += self.sys.sync_interface(dryrun=dryrun)
        res += self.sys.sync_iprules(dryrun=dryrun)
        for peer in self.peers.values():
            self.log.debug("syncing peer %s", peer.name_and_id)
            try:
                peer_res = self.sys.sync_peer(peer.id, dryrun)
            except Exception as ex:
                peer_res = repr(ex)
            res.append(peer_res)
        res += self.sys.remove_unknown(dryrun=dryrun)
        res = list(filter(None, res))
        if res and not firstrun:
            pass
            # self.log.info("sync: %s" % (res,))
            # currently this global sync is all we have; later it will again be
            # expected to have no results and the below log line can be
            # restored:
        #            self.log.warn(
        #                "WARNING: peers %s out of sync: \n%s",
        #                ('were', 'are')[dryrun],
        #                res,
        #            )
        return res

    @DualUse.method()
    def rediscover(self):
        self.discover.listen([])
        self._instruct_zeroconf()
        return ",".join(map(str, self.state.system_state.current_ips))

    @DualUse.method()
    def release_gateway(self):
        """
        Release the current gateway
        """
        return str(yamlrepr(self.state.event_RELEASE_GATEWAY()))

    @DualUse.method()
    def bp(self):
        """
        Call pdb.set_trace()
        """
        pdb.set_trace()

    @DualUse.method()
    @click.option(
        '-m', '--monolithic', is_flag=True, help="Run in monolithic mode"
    )
    @click.option(
        '--no-dbus',
        is_flag=True,
        help="Run in monolithic mode without dbus (experimental/unsupported)",
    )
    def run(self, monolithic, no_dbus=False):
        """
        Run GLib main loop (default if no command specified)
        """

        if not no_dbus:
            system_bus = pydbus.SystemBus()
            system_bus.publish(_ORGANIZE_DBUS_NAME, self)
            main_loop = GLib.MainLoop()

        if monolithic or no_dbus:
            self.discover = Discover()
            self.discover.callbacks.append(self.process_descriptor)
            self.publish = Publish()
        else:
            self.discover = system_bus.get(
                _DISCOVER_DBUS_NAME, _DISCOVER_DBUS_PATH
            )
            self.publish = system_bus.get(
                _PUBLISH_DBUS_NAME, _PUBLISH_DBUS_PATH
            )

        # remove old listener, if there is one
        self.discover.listen([])

        self.get_new_system_state()
        self.sys.start_monitor()
        self._instruct_zeroconf()
        self.sync()

        if not no_dbus:
            self.log.info("calling GLib.MainLoop().run()")
            main_loop.run()

    def _instruct_zeroconf(self):

        descriptors = {}
        vf: int = int(time.time())
        for net, ips in self.state.system_state.current_subnets.items():
            desc = {
                k: str(v)
                for k, v in self._construct_service_descriptor(
                    ",".join(str(ip) for ip in ips), vf
                )
                ._dict()
                .items()
            }
            for ip in ips:
                descriptors[str(ip)] = desc
        current_ips = list(map(str, self.state.system_state.current_ips))
        self.log.info(
            "discovering on {ips} and publishing {pub}".format(
                ips=current_ips,
                pub='on same'
                if list(descriptors.keys()) == current_ips
                else descriptors,
            )
        )
        self.discover.listen(current_ips)
        self.publish.listen(descriptors)
        self._latest_descriptors = descriptors
        self.log.info("Current IP(s): {}".format(current_ips))
        self.log.info(
            "Current descriptors: {}".format(self._latest_descriptors)
        )

    @DualUse.method(opts=(click.argument('query', type=str),))
    def show_peer(self, query):
        """
        Returns peer description string from query for vk, hostname, or IP.
        """
        peer = self.peers.query(query)
        return (
            peer.show(self.sys.get_stats().get(str(peer.descriptor.pk)))
            if peer
            else "No peer matched query %r" % (query,)
        )

    @DualUse.method(opts=(click.argument('query', type=str),))
    def peer_descriptor(self, query):
        """
        Returns peer descriptor string from query for vk, hostname, or IP.
        """
        peer = self.peers.query(query)
        return str(peer.descriptor) if peer else ''

    def process_descriptor_string(self: Organize, descriptor: str):

        self.log.debug("about to parse descriptor: %r", descriptor)
        try:
            descriptor = Descriptor.parse(descriptor)
        except Exception as ex:
            self.log.info(
                "organize failed to parse descriptor because %r (descriptor "
                "was %r)" % (ex, descriptor)
            )
            return

        if descriptor is None:
            self.log.info(
                "organize failed to parse descriptor (descriptor was %r)"
                % (descriptor,)
            )
            return

        return self.process_descriptor(descriptor)

    def process_descriptor(self: Organize, descriptor: Descriptor):

        if not descriptor.verify_signature():
            self.log.info(
                "Discarded descriptor with invalid signature: %r"
                % (descriptor,)
            )
            return

        res = self.state.event_INCOMING_DESCRIPTOR(descriptor)

        # if res.writes:
        #    # this should happen with triggers in the event engine
        #    self.sync()
        return str(yamlrepr(res))

    def get_vk_by_name(self, hostname):
        return self.peers.with_hostname(hostname).id

    def peer_ids(self, which):
        peers = self.peers
        if which == 'disabled':
            peers = peers.limit(enabled=False)
        elif which == 'enabled':
            peers = peers.limit(enabled=True)
        else:
            assert which == 'all'
        return list(peers.keys())

    def dump_state(self, interactive, dbus_context):
        if dbus_context.is_authorized(
            'local.vula.organize1.Debug.dump_state',
            details={},
            interactive=interactive,
        ):
            return repr(yamlrepr(self.state._dict()))
        else:
            return "Forbidden"

    def test_auth(self, interactive, dbus_context):
        if dbus_context.is_authorized(
            'local.vula.organize1.Debug.test_auth',
            details={},
            interactive=interactive,
        ):
            return "OK"
        else:
            return "Forbidden"

    def set_peer(self, vk, path, value):
        res = self.state.event_USER_EDIT('SET', ['peers', vk] + path, value)
        return str(jsonrepr(res))

    def remove_peer(self, query):
        return str(yamlrepr(self.state.event_USER_REMOVE_PEER(query)))

    def peer_addr_add(self, vk, ip):
        return str(yamlrepr(self.state.event_USER_PEER_ADDR_ADD(vk, ip)))

    def peer_addr_del(self, vk, ip):
        return str(yamlrepr(self.state.event_USER_PEER_ADDR_DEL(vk, ip)))

    def show_prefs(self):
        return str(yamlrepr(self.state.prefs))

    def set_pref(self, pref, value):
        # this should call event_EDIT_PREF instead of event_USER_EDIT; this
        # as-yet unwritten event should call an action which should trigger
        # get_new_system_state to cause, eg, removal of allowed subnets
        # or interfaces to take effect immediately.
        return str(self.state.event_USER_EDIT('SET', ['prefs', pref], value))

    def add_pref(self, pref, value):
        return str(self.state.event_USER_EDIT('ADD', ['prefs', pref], value))

    def remove_pref(self, pref, value):
        return str(
            self.state.event_USER_EDIT('REMOVE', ['prefs', pref], value)
        )

    @DualUse.method()
    def eventlog(self):
        return "\n".join(
            "{event}: {actions} {writes} {triggers}".format(
                event=result.event[0],
                actions=[action[0] for action in result.actions],
                writes=[write[0] for write in result.writes],
                triggers=[trigger[0] for trigger in result.triggers],
            )
            for result in map(Result, self.state.event_log)
        )


Organize.cli.add_command(PeerCommands.cli, name='peer')
Organize.cli.add_command(PrefsCommands.cli, name='prefs')

main = Organize.cli

if __name__ == "__main__":
    main()
