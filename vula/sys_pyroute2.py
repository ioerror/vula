from ipaddress import ip_address, ip_network
from pyroute2 import IPRoute
from pyroute2.netlink.exceptions import NetlinkError
from socket import AddressFamily
from .wg import Interface as WgInterface
from .peer import Peer
from .constants import _LINUX_MAIN_ROUTING_TABLE, IPv4_GW_ROUTES
import threading
from pyroute2 import IPRSocket
from pprint import pprint
from .common import bp

# FIXME: find where the larger canonical version of this table lives
SCOPES = {0: 'global', 253: 'static'}


class Sys(object):
    """
    This  object provides all of the pyroute2-based system integration.
    Organize (and everything else) should only call pyroute2 via this object.

    This is currently our only implementation of our still-evolving Sys
    interface. We should reduce the number of public methods here to a minimum,
    and later we can reimplement this object using other means on other
    platforms.
    """

    def __init__(self, organize):
        self.organize = organize
        self.log = organize.log if organize else None
        self.wg_name = self.organize.interface if organize else None
        self.ipr = IPRoute()
        self.wgi = WgInterface(self.wg_name, ipr=self.ipr)
        self._monitor_thread = None
        self._stop_monitor = False

    def start_monitor(self):
        self._stop_monitor = False
        if self._monitor_thread is None:
            self._monitor_thread = threading.Thread(
                target=self._monitor
            )  # , args=(1,))
            self._monitor_thread.start()

    def get_stats(self):
        self.wgi.query()
        stats = {peer.public_key: peer['stats'] for peer in self.wgi.peers}
        return stats

    def stop_monitor(self):
        self._stop_monitor = True

    def _monitor(self):

        ip = IPRSocket()
        ip.bind()
        while True:
            msg = ip.get()
            if len(msg) != 1:
                self.log.info(
                    "BUG: got message with non-1 length %r which we didn't expect ever happens",
                    msg,
                )
                continue
            event = msg[0].get('event')
            if event in [
                'RTM_DELADDR',
                'RTM_NEWADDR',
                'RTM_DELROUTE',
                'RTM_NEWROUTE',
            ]:
                self.log.debug("acting on netlink message: %r", msg)
                self.get_new_system_state()
            elif event == 'RTM_NEWNEIGH':
                # this happens often, so we don't even debug log it
                pass
            else:
                self.log.debug(
                    "ignoring netlink message type %r (%s bytes)",
                    event,
                    len(str(msg)),
                )
            if self._stop_monitor:
                self.log.info("Stopping netlink monitor thread")
                break
        self._monitor_thread = None
        ip.close()

    def _get_system_state(self):

        "WIP"

        addrs = self.ipr.get_addr()

        gateways = list(
            set(
                r.get_attrs('RTA_GATEWAY')[0]
                for r in self.ipr.get_routes()
                if r.get_attrs('RTA_GATEWAY')
            )
        )

        system_links = {
            dict(link['attrs'])['IFLA_IFNAME']: dict(link['attrs'])[
                'IFLA_CARRIER'
            ]  # unused
            for link in self.ipr.get_links()
        }

        current_subnets = {}

        for a in addrs:
            addr = ip_address(dict(a['attrs'])['IFA_ADDRESS'])
            iface = dict(a['attrs']).get('IFA_LABEL', '')
            this_subnet = ip_network(
                "%s/%s" % (addr, a['prefixlen']), strict=False
            )
            if not any(
                [
                    iface.startswith(prefix)
                    for prefix in self.organize.prefs.iface_prefix_allowed
                ]
            ):
                continue

            if any(
                addr in subnet
                for subnet in self.organize.prefs.subnets_allowed
            ) and not any(
                addr in subnet
                for subnet in self.organize.prefs.subnets_forbidden
            ):
                current_subnets.setdefault(this_subnet, []).append(addr)

        return current_subnets, gateways

    def get_new_system_state(self):
        return self.organize.get_new_system_state()

    def sync_interface(self, dryrun=False):
        return self.wgi.sync_interface(
            private_key=str(self.organize._keys.wg_Curve25519_sec_key),
            listen_port=self.organize.port,
            fwmark=self.organize.fwmark,
            dryrun=dryrun,
        )

    def sync_peer(self, vk: str, dryrun: bool = False):
        """
        Syncs peer's wg config and routes. Returns a string.
        """
        peer = self.organize.peers[vk]
        res = []
        if peer.enabled:
            self.log.debug("syncing enabled peer %s", peer.name)
            csidh_psk = self.organize.csidh_dh(peer.descriptor.c)
            res.append(
                self.wgi.apply_peerconfig(peer.wg_config(csidh_psk), dryrun)
            )
            res.append(
                self.sync_routes(
                    peer.routes, table=self.organize.table, dryrun=dryrun,
                )
            )
            if peer.use_as_gateway:
                res.append(
                    self.sync_routes(
                        [*IPv4_GW_ROUTES],
                        table=_LINUX_MAIN_ROUTING_TABLE,
                        dryrun=dryrun,
                    )
                )
            self.log.debug("organize.Peer.sync result: %r", res)
        else:
            # FIXME: this should go away with triggers, but hasn't yet?
            self.remove_unknown()
        res = filter(None, res)
        return "\n".join(res)

    def sync_iprules(self, dryrun=False):
        routing_table = self.organize.table
        mark = self.organize.fwmark
        priority = self.organize.ip_rule_priority
        not_flag = 0x02
        res = []
        ip_version = {AddressFamily.AF_INET: "4", AddressFamily.AF_INET6: "6"}
        for family in ip_version.keys():
            existing_rule = [
                rule
                for rule in self.ipr.get_rules(family=family)
                if dict(rule['attrs'])['FRA_TABLE'] == routing_table
                and dict(rule['attrs'])['FRA_FWMARK'] == mark
                and dict(rule['attrs'])['FRA_PRIORITY'] == priority
                and rule['header']['flags'] == not_flag
            ]
            if existing_rule:
                self.log.debug(
                    "Found expected existing rule: (%s)", existing_rule
                )
            else:
                if not dryrun:
                    self.ipr.rule(
                        'add',
                        table=routing_table,
                        priority=priority,
                        fwmark=mark,
                        family=family,
                        flags=not_flag,
                    )
                res.append(
                    "ip -{af} rule add not from all fwmark 0x{mark:x} lookup {table}".format(
                        af=ip_version[family], mark=mark, table=routing_table
                    )
                )
        return res

    def remove_wg_peer(self, pk, dryrun=False):
        return self.wgi.apply_peerconfig(
            dict(public_key=pk, remove=True), dryrun
        )

    def remove_routes(self, dests, table=None, dev=None, dryrun=False):
        """
        Idempotently remove route(s)

        Dests is a list of cidr notation strings.

        Returns a string describing what was (or would be) done.
        """
        if table is None:
            table = self.organize.table
        if dev is None:
            dev = self.wg_name
        res = []
        for route in self.get_route_entries(dests, table, dev):
            if not dryrun:
                self.ipr.route("del", **route)
            res.append(
                "ip route del {dst} dev {dev} table {table}".format(
                    dst=route['dst'], dev=dev, table=route['table'],
                )
            )
        return "\n".join(res)

    def get_route_entries(self, dests=None, table=None, dev=None):
        """
        Query for routes. Returns a dict suitable for applying (with **) to
        ipr's route del function.

        Unlike passing ipr.get_routes a dst argument, this only returns
        specific routes which actually exist (as opposed to synthesizing a
        route possibly from a larger match, and returning it with the wrong
        table, as get_routes does).
        """
        current_routes = self.ipr.get_routes()
        if dev:
            oif = self.ipr.link_lookup(ifname=dev)[0]
        # flatten attrs list to dict (api allows duplicate keys - but we don't)
        [r.update(attrs=dict(r['attrs'])) for r in current_routes]
        # install dst key with cidr notation
        [
            r.update(dst=r['attrs']['RTA_DST'] + "/" + str(r['dst_len']))
            for r in current_routes
            if 'RTA_DST' in r['attrs']
        ]
        res = [
            dict(
                dst=r['dst'],
                table=r['attrs']['RTA_TABLE'],
                oif=r['attrs']['RTA_OIF'],
                scope=r['scope'],
            )
            for r in current_routes
            if 'dst' in r
            and (dests is None or r['dst'] in dests)
            and (table is None or r['attrs']['RTA_TABLE'] == table)
            and (dev is None or r['attrs']['RTA_OIF'] == oif)
        ]
        return res

    def remove_unknown(self, dryrun=False):
        """
        This is currently the code path where disabled and removed peers get
        their routes and wg peer configs removed. In the future, deferred
        actions from the event engine should remove the specific things that we
        know need to be removed, and then this method will actually only be
        used to remove rogue entries.
        """
        routing_table = self.organize.table
        res = []
        enabled_pks = [
            str(peer.descriptor.pk)
            for peer in self.organize.peers.limit(enabled=True).values()
        ]
        for peer in self.wgi.peers:
            if peer['public_key'] not in enabled_pks:
                if not dryrun:
                    res.append(self.remove_wg_peer(peer['public_key'], dryrun))
                    self.log.info(
                        "Removing unexpected peer pk: (%s)", peer['public_key']
                    )
                res.append(
                    "wg set {interface} peer {pk} remove".format(
                        interface=self.wg_name, pk=peer['public_key']
                    )
                )
        expected_routes = [
            str(dst)
            for peer in self.organize.peers.limit(enabled=True).values()
            for dst in peer.allowed_ips
        ]

        current_routes = self.ipr.get_routes()
        [r.update(attrs=dict(r['attrs'])) for r in current_routes]
        our_current_routes = [
            r
            for r in current_routes
            if r['attrs']['RTA_TABLE'] == self.organize.table
        ]
        for route in our_current_routes:
            dst = route['attrs']['RTA_DST'] + "/" + str(route['dst_len'])
            if dst not in expected_routes:
                scope = route['scope']
                if not dryrun:
                    self.log.info("Removing unexpected route: (%s)", dst)
                    self.ipr.route(
                        'del', table=routing_table, dst=str(dst), scope=scope
                    )
                if scope in SCOPES:
                    # this is strictly cosmetic; the printed "ip route" command is runnable with the scope as an integer too
                    scope = SCOPES[scope]
                res.append(
                    "ip route del {dst} table {table} scope {scope}".format(
                        dst=dst, table=routing_table, scope=scope
                    )
                )
        if not self.organize.peers.limit(use_as_gateway=True, enabled=True):

            default_routes = [
                r
                for r in current_routes
                if r['attrs'].get('RTA_TABLE') == _LINUX_MAIN_ROUTING_TABLE
                and r['attrs'].get('RTA_DST') in ('0.0.0.0', '128.0.0.0')
                and r['attrs'].get('RTA_DST')
            ]
            for route in default_routes:
                dst = route['attrs']['RTA_DST'] + "/" + str(route['dst_len'])
                scope = route['scope']
                if not dryrun:
                    self.log.info("Removing unexpected route: (%s)", dst)
                    self.ipr.route(
                        'del',
                        table=_LINUX_MAIN_ROUTING_TABLE,
                        dst=str(dst),
                        scope=scope,
                    )
                if scope in SCOPES:
                    # this is strictly cosmetic; the printed "ip route" command is runnable with the scope as an integer too
                    scope = SCOPES[scope]
                res.append(
                    "ip route del {dst} table {table} scope {scope}".format(
                        dst=dst, table=_LINUX_MAIN_ROUTING_TABLE, scope=scope
                    )
                )

        return res

    def sync_routes(self, dests, table, dryrun=False):
        """
        Takes a list of cidr notation dests and a routing table, and ensures
        those routes are configured there. Returns a string.
        """
        res = []
        self.log.debug("looking for routes for: %r", dests)

        oif_idx = self.ipr.link_lookup(ifname=self.wg_name)

        system_state = self.organize.state.system_state

        for dest in map(ip_network, dests):
            routes = self.ipr.route("show", dst=str(dest), table=table)
            if not routes:
                src = None
                for net in system_state.current_subnets:
                    # note: current_subnets is consulted to find a source
                    # address but NOT consulted regarding the destination.
                    # (for pinned peers, we want to add IPs from
                    # non-current subnets here; they only need to be in a
                    # current subnet the first time they're seen)
                    if dest.version == net.version and dest.subnet_of(net):
                        src = system_state.current_subnets[net][0]
                        # select the first local IP we have in the first
                        # subnet. (it would be more correct to use the
                        # longest-prefix-matching subnet... but not
                        # bothering with that for now.)
                        break
                        # further note: this current_subnets logic
                        # doesn't belong here at all; will refactor
                        # this into system state soon.
                res.append(
                    f"ip route add {dest} dev {self.wg_name} proto static scope link%s table {table}"
                    % (f" src {src}" if src else "")
                )
                if not dryrun:
                    self.log.info("[#] %s", str(res[-1]))
                    self.ipr.route(
                        "add",
                        dst=str(dest),
                        oif=oif_idx,
                        table=table,
                        scope='link',
                        prefsrc=str(src) if src else None,
                    )
            else:
                for route in routes:
                    self.log.debug("found existing route for %s", dest)

        return "\n".join(res)
