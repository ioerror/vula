from __future__ import annotations

import json
import time
from base64 import b64encode
from datetime import timedelta
from io import StringIO
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from typing import List

import click
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey
from schema import And, Optional, Regex, Schema, Use

from .constants import _VULA_ULA_SUBNET

from .common import (
    Bug,
    ConsistencyError,
    Flexibool,
    Length,
    attrdict,
    b64_bytes,
    comma_separated_Nets,
    use_ip_address,
    use_comma_separated_IPv4s,
    use_comma_separated_IPv6s,
    packable_types,
    sort_LL_first,
    format_byte_stats,
    int_range,
    organize_dbus_if_active,
    queryable,
    schemadict,
    schemattrdict,
    serializable,
    yamlrepr,
    yamlrepr_hl,
)
from .engine import Result
from .notclick import (
    DualUse,
    blue,
    bold,
    echo_maybepager,
    green,
    red,
    shell_complete_helper,
    yellow,
)

_qrcode = None


@DualUse.object()
class Descriptor(schemattrdict, serializable):
    """
    Descriptors are the objects which are communicated between publish
    and discover (via mDNS) and between discover and organize (via strings).
    """

    schema = Schema(
        {
            Optional('p'): use_ip_address,
            Optional('v4a'): use_comma_separated_IPv4s,
            Optional('v6a'): use_comma_separated_IPv6s,
            'pk': b64_bytes.with_len(32),
            'c': b64_bytes.with_len(64),
            'hostname': And(
                str,
                # fixme: this should also ensure labels don't
                #  start or end with a dash, as per RFC1123
                Regex('^[a-zA-Z0-9.-]+$'),
                lambda name: 0 < len(name) < 256,
            ),
            'port': int_range(1, 65535),
            'vk': b64_bytes.with_len(32),
            'dt': Use(int),
            'vf': Use(int),
            'r': Use(
                comma_separated_Nets
            ),  # AllowedIPs may be set from this in the future; fixme
            'e': Flexibool,
            Optional('s'): b64_bytes.with_len(64),
        }
    )

    default = dict(r="")

    @classmethod
    def from_zeroconf_properties(cls, props: dict):
        """
        This instantiates a descriptor from a dictionary of bytes values, as
        the zeroconf library gives us.

        This function is tested via as_zeroconf_properties's doctest below.

        This function should be called from within a try block, as invalid
        descriptors with raise an exception.
        """
        data = {}
        for k, v in props.items():
            k = k.decode()
            typ = cls.schema._schema.get(k) or cls.schema._schema.get(
                Optional(k)
            )
            if typ := packable_types.get(typ):
                # here we have a type that knows how to pack and unpack itself
                data[k] = typ(v)
            elif v is None:
                data[k] = ''
            else:
                data[k] = v.decode()
        return cls(**data)

    @property
    def as_zeroconf_properties(self):
        r"""
        This returns the descriptor as a dictionary of bytes, for sending to
        zeroconf.

        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> Descriptor.parse(_TEST_DESC_UNSIGNED).as_zeroconf_properties
        {b'r': b'', b'c': b'NnoGEZ4W+d6TE22+Qyau0LF513FM43EagOP9aiSX9KhTCS1Gryt7qDoM04j7p0KQRJxwkcPEO/MpIJE5/bJKYQ==', b'dt': b'86400', b'e': b'0', b'hostname': b'vula-bookworm-test1.local.', b'p': b'\xfd\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01', b'pk': b'3w5/xje5jsdUCX30JfS/L/bMuwZRniK69dAVprN7t3c=', b'port': b'5354', b'v4a': b'\nY\x00\x02', b'v6a': b'\xfd\xff\xff\xff\xff\xdf\x98\x9f$\xcf\x0b\xda\x12b\xcf\xc6\xfe\x80\x00\x00\x00\x00\x00\x00\xbc\x92M\xff\xfe\x82\x03\r\xfdT\xf2z\x17\xc1:a\x00\x00\x00\x00\x00\x00\x00\x02', b'vf': b'1743974365', b'vk': b'afToKyN29ubu4DkhUMLoGIt5WjbsgEHYuccNtxvbjmA='}

        # Full round trip:
        >>> str(Descriptor.from_zeroconf_properties(
        ...         Descriptor.parse(_TEST_DESC_UNSIGNED).as_zeroconf_properties)
        ... ) == _TEST_DESC_UNSIGNED
        True
        """
        data = {}
        for k, v in self.items():
            typ = self.schema._schema.get(k) or self.schema._schema.get(
                Optional(k)
            )
            data[k.encode()] = (
                v.packed if packable_types.get(typ) else str(v).encode()
            )
        return data

    @classmethod
    def parse(cls, desc: str) -> Descriptor:
        """
        Parse the *descriptor* string line into a dictionary-like object. Carefully.

        >>> from vula.constants import _TEST_DESC
        >>> _TEST_DESC == str(Descriptor.parse(_TEST_DESC))
        True
        """
        try:
            split_desc: List = desc.split(";")
            dir_desc: dict = dict(
                val.split("=", maxsplit=1)
                for val in [kv.strip() for kv in split_desc]
                if len(val) > 1
            )
            descriptor: Descriptor = cls(dir_desc)
        except ValueError:
            raise
            # log.info("Unable to parse descriptor: %s (%r)", error, descriptor)
            return None
        return descriptor

    def _build_sig_buf(self: Descriptor) -> bytes:
        return " ".join(
            "%s=%s;" % (k, v) for k, v in sorted(self.items()) if k != 's'
        ).encode()

    def __str__(self):
        return " ".join("%s=%s;" % kv for kv in sorted(self.items()))

    @property
    def id(self):
        """
        This returns the peer ID (aka the verify key, base64-encoded).
        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> d = Descriptor.parse(_TEST_DESC_UNSIGNED)
        >>> d.id
        'afToKyN29ubu4DkhUMLoGIt5WjbsgEHYuccNtxvbjmA='
        """
        return str(self.vk)

    @property
    def ephemeral(self):
        """
        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> d = Descriptor.parse(_TEST_DESC_UNSIGNED)
        >>> d.ephemeral
        0
        """
        return self.e

    @property
    def valid(self):
        # XXX: placeholder until this is merged with other class with signature validation etc
        # ^^^
        return self.verify_signature()

    @property
    def IPv4addrs(self):
        """
        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> d = Descriptor.parse(_TEST_DESC_UNSIGNED)
        >>> d.IPv4addrs
        [IPv4Address('10.89.0.2')]
        """
        return list(getattr(self, 'v4a', ()))

    @property
    def IPv6addrs(self):
        """
        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> d = Descriptor.parse(_TEST_DESC_UNSIGNED)
        >>> d.IPv6addrs # doctest: +NORMALIZE_WHITESPACE
        [IPv6Address('fdff:ffff:ffdf:989f:24cf:bda:1262:cfc6'),
         IPv6Address('fe80::bc92:4dff:fe82:30d'),
         IPv6Address('fd54:f27a:17c1:3a61::2')]
        """
        return list(getattr(self, 'v6a', ()))

    @property
    def all_addrs(self):
        return self.IPv6addrs + self.IPv4addrs

    def sign(self, seed) -> Descriptor:
        signing_key: SigningKey = SigningKey(seed=seed)
        buf_to_sign: bytes = self._build_sig_buf()
        sig: bytes = signing_key.sign(buf_to_sign).signature
        descriptor = Descriptor(self, s=b64encode(sig).decode())
        return descriptor

    def verify_signature(self) -> bool:
        """
        Verifies the signature.
        Returns true if valid, false if invalid.

        Missing signature:
        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> desc = Descriptor.parse(_TEST_DESC_UNSIGNED)
        >>> assert desc.verify_signature() is False

        Valid signature:
        >>> from vula.constants import _TEST_DESC
        >>> desc = Descriptor.parse(_TEST_DESC)
        >>> assert desc.verify_signature() is True

        Invalid signature:
        >>> desc = Descriptor(desc, port=desc['port'] + 1)
        >>> assert desc.verify_signature() is False
        """
        sig = self.get('s')
        if not sig:
            return False
        verify_public_key = VerifyKey(self.vk)
        buf_to_verify: bytes = self._build_sig_buf()
        try:
            verify_public_key.verify(buf_to_verify, sig)
            return True
        except BadSignatureError:
            return False

    def make_peer(self: Descriptor, **kwargs) -> Peer:
        peer = dict(
            descriptor=self,
            petname="",
            pinned=False,
            enabled=True,
            verified=False,
            nicknames={self.hostname: True},
            IPv4addrs={ip: True for ip in self.IPv4addrs},
            IPv6addrs={ip: True for ip in self.IPv6addrs},
            use_as_gateway=False,
        )
        peer.update(**kwargs)
        return Peer(peer)

    @property
    def qr_code(self):
        """
        This generates a QR-Code and prints it.
        The data that is encoded within the QR-Code is
        given by this functions parameter.

        It returns a string.
        """
        global _qrcode
        if _qrcode is None:
            import qrcode as _qrcode
        sio = StringIO()
        qr = _qrcode.QRCode()
        qr.add_data(data="local.vula:desc:" + str(self))
        qr.print_ascii(out=sio)
        sio.seek(0)
        return sio.read()


class Peer(schemattrdict):
    schema = Schema(
        And(
            {
                'descriptor': Use(Descriptor),
                'petname': str,
                'nicknames': {Optional(str): Flexibool},
                'IPv4addrs': {Optional(Use(IPv4Address)): Flexibool},
                'IPv6addrs': {Optional(Use(IPv6Address)): Flexibool},
                'enabled': Flexibool,
                'verified': Flexibool,
                'pinned': Flexibool,
                Optional('use_as_gateway'): Flexibool,
                Optional('_allow_unsigned_descriptor'): Flexibool,
            },
            # lambda peer:
            # peer['descriptor'].verify_signature() or peer.get('_allow_unsigned_descriptor')
        )
    )

    # Peers are currently only instantiated by Descriptor.make_peer, default is
    # there.
    default = None

    @property
    def id(self):
        "This returns the peer ID (aka the verify key, as a base64 string)"
        return self.descriptor.id

    @property
    def wg_pk(self):
        "WireGuard public key."
        return self.descriptor.pk

    @property
    def name(self):
        """
        This returns the best name, for display purposes.

        It is either the petname, or the last name announced, or, if the last
        name announced is disabled, another enabled name.
        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> peer = Descriptor.parse(_TEST_DESC_UNSIGNED).make_peer(petname='george')
        >>> peer.name
        'george'
        """
        latest = self.descriptor.hostname
        return self.get('petname') or (
            latest
            if self.nicknames[self.descriptor.hostname]
            else self.enabled_names[0]
            if self.enabled_names
            else "<unnamed>"
        )

    @property
    def other_names(self):
        """
        Returns a sorted list of all names other than self.name

        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> peer = Descriptor.parse(_TEST_DESC_UNSIGNED).make_peer(
        ...      petname='abc', nicknames=dict(xyz=True,xxx=False,yyy=True))
        >>> peer.other_names
        ['xyz', 'yyy']
        """
        return list(
            sorted(
                {n for n, e in self.nicknames.items() if e} - set([self.name])
            )
        )

    @property
    def name_and_id(self):
        """
        Returns the name and ID of the peer.

        >>> from vula.constants import _TEST_DESC_UNSIGNED
        >>> peer = Descriptor.parse(_TEST_DESC_UNSIGNED).make_peer(
        ...                                         petname='abc')
        >>> peer.name_and_id
        'abc (afToKyN29ubu4DkhUMLoGIt5WjbsgEHYuccNtxvbjmA=)'
        """
        return "%s (%s)" % (self.name, self.id)

    @property
    def enabled_names(self):
        return sorted(
            set(
                ([self.petname] if self.petname else [])
                + [n for n in self.nicknames if self.nicknames[n]]
            )
        )

    @property
    def enabled_ips(self):
        return (
            [self.primary_ip]
            + [ip for ip, on in self.IPv6addrs.items() if on]
            + [ip for ip, on in self.IPv4addrs.items() if on]
        )

    @property
    def disabled_ips(self):
        return [ip for ip, on in self.IPv6addrs.items() if not on] + [
            ip for ip, on in self.IPv4addrs.items() if not on
        ]

    @property
    def primary_ip(self):
        return self.descriptor.p

    @property
    def enabled_ips_str(self):
        return [str(ip) for ip in self.enabled_ips]

    @property
    def routable_ips(self):
        return [
            ip
            for ip in self.enabled_ips
            if not (ip.version == 6 and ip.is_link_local)
        ]

    @property
    def routes(self):
        return [
            ip_network("%s/%s" % (ip, ip.max_prefixlen))
            for ip in self.routable_ips
        ]

    @property
    def _wg_allowed_ips(self):
        res = [
            ip_network("%s/%s" % (ip, ip.max_prefixlen))
            for ip in self.routable_ips
        ]
        if self.use_as_gateway:
            res.append(ip_network("0.0.0.0/0"))
            res.append(ip_network("::/0"))
        return list(map(str, res))

    @property
    def endpoint_addr(self):
        if ips := sort_LL_first(
            i for i in self.enabled_ips if i not in _VULA_ULA_SUBNET
        ):
            return ips[0]
        return ip_address('0.0.0.0')

    @property
    def endpoint(self):
        """
        Return endpoint host:port address, for display purposes.
        """
        return "%s:%s" % (
            f"[{a}]" if (a := self.endpoint_addr).version == 6 else a,
            self.descriptor.port,
        )

    def wg_config(self: Peer, ctidh_psk):
        return attrdict(
            public_key=str(self.descriptor.pk),
            endpoint_addr=str(self.endpoint_addr),
            endpoint_port=self.descriptor.port,
            allowed_ips=self._wg_allowed_ips,
            preshared_key=ctidh_psk,
        )

    def show(self, stats=None):
        green_or_yellow = (
            green if self.pinned and self.verified and self.enabled else yellow
        )
        return "\n  ".join(
            bold(label) + ': ' + str(value) if label else str(value)
            for label, value in {
                green_or_yellow('peer'): green_or_yellow(self.name),
                'id': self.id,
                red('warning'): (
                    None if stats else red('wireguard peer is not configured')
                ),
                'other names': ", ".join(self.other_names),
                'status': " ".join(
                    filter(
                        None,
                        [
                            (red("disabled"), green("enabled"))[self.enabled],
                            (yellow("unpinned"), green("pinned"))[self.pinned],
                            (
                                (red if self.pinned else yellow)("unverified"),
                                green("verified"),
                            )[self.verified],
                            ('', bold(blue("gateway")))[self.use_as_gateway],
                        ],
                    )
                ),
                'endpoint': self.endpoint,
                'primary ip': self.primary_ip,
                'allowed ips': ", ".join(self._wg_allowed_ips),
                'disabled ips': ", ".join(map(str, self.disabled_ips)),
                'latest signature': (
                    str(
                        timedelta(
                            seconds=int(time.time() - self.descriptor.vf)
                        ),
                    )
                    + ' ago'
                ),
                'latest handshake': (
                    str(
                        timedelta(
                            seconds=int(
                                time.time() - stats['latest_handshake']
                            )
                        ),
                    )
                    + ' ago'
                    if stats and stats.get('latest_handshake')
                    else yellow('none')
                ),
                'transfer': (
                    stats
                    and sum(stats.values())
                    and "{rx_bytes} received, {tx_bytes} sent".format(
                        **format_byte_stats(stats)
                    )
                ),
                'wg pubkey': self.descriptor.pk,
            }.items()
            if value not in (None, False, '')
        )


class Peers(yamlrepr, queryable, schemadict):
    """
    A dictionary of peers. Note that, despite being the home of the conflict
    detection code, a Peers object can be valid (from a schema standpoint) even
    while containing conflicts. The schema of a SystemState object uses this
    conflict detection code to ensure that the Peers object within a
    SystemState does not contain conflicts.
    """

    schema = Schema(
        {
            Optional(And(str, Length(44))): Use(Peer),
        },
    )

    def with_hostname(self: Peers, name: str):
        "Return peer with given hostname (among all of its enabled names)"
        res = self.limit(enabled=True).by('nicknames').get(name, [])
        if len(res) > 1:
            raise Bug(
                # this should not be possible, as both the state logic and
                # schema prevent it
                "BUG: multiple hosts with the same name: %r"
                % (res,)
            )
        if len(res) < 1:
            raise KeyError("Hostname %r not found." % (name,))
        return res[0]

    def with_ip(self, ip):
        "Return peer with given IP address"
        ip = ip_address(ip)
        res = self.limit(enabled=True).by('enabled_ips').get(ip, [])
        if len(res) > 1:
            raise ConsistencyError(
                # this should also not be possible, because the state logic
                # prevents it (though the schema doesn't yet)
                "BUG: multiple hosts with the same IP: %r"
                % (res,)
            )
        if len(res) < 1:
            raise ValueError("No peer with IP %r" % (ip,))
        return res[0]

    @property
    def conflicts(self):
        "returns comma-separated list of colliding peer ids"
        enabled_gws = list(
            self.limit(use_as_gateway=True, enabled=True).values()
        )
        res = ",".join(
            [
                peer.id
                for peer in self.limit(enabled=True).values()
                if self.conflicts_for_descriptor(peer.descriptor)
            ]
            + [peer.id for peer in enabled_gws if len(enabled_gws) > 1]
        )
        return res

    def conflicts_for_descriptor(self, desc):
        """
        Returns list of enabled vula peers where a descriptor has a conflicting
        wg_pk, hostname, or IP address field (ignoring itself).

        """
        return list(
            {
                conflict.id: conflict
                for conflict in self.limit(enabled=True)
                .by('enabled_names')
                .get(desc.hostname, [])
                + self.limit(enabled=True).by('wg_pk').get(desc.pk, [])
                + sum(
                    (
                        self.limit(enabled=True).by('IPv4addrs').get(ip, [])
                        for ip in desc.IPv4addrs
                    ),
                    [],
                )
                + sum(
                    (
                        self.limit(enabled=True).by('IPv6addrs').get(ip, [])
                        for ip in desc.IPv6addrs
                    ),
                    [],
                )
                if conflict.id != desc.id
            }.values()
        )

    def query(self, query):
        """
        Returns peer by vk, hostname, or IP. None if no match.
        """
        peer = (
            self.by('id').get(query)
            or self.limit(enabled=True).by('enabled_names').get(query)
            or self.limit(enabled=True).by('enabled_ips_str').get(query)
        )
        if peer:
            assert len(peer) == 1, ("this should not be possible:", peer)
            return peer[0]
        else:
            return None


def _ac_get_peer_ids(ctx, args, incomplete):
    organize = (
        ctx.meta.get('Organize', {}).get('magic_instance')
        or organize_dbus_if_active()
    )
    return organize.peer_ids('all')


@DualUse.object(
    short_help="View and modify peer information",
    invoke_without_command=True,
)
@click.pass_context
class PeerCommands(object):
    """
    Commands to view and modify peer information.

    When "peer" is the top-level command, its subcommands communicate with
    organize via DBus. This is the normal way to use these commands (e.g., you
    can run "vula peer show").

    At this point in development, "peer" may also be run as a subcommand of the
    "organize" command, in which case it will instantiate and operate on the
    organize object directly. In the case of the "set" and "remove" peer
    subcommands, this only makes sense when there isn't an organize daemon
    process running (as the daemon process will overwrite the state file
    written by the "organize peer ..." command process without ever reading its
    contents). Note that we do not currently check to ensure that there is not
    an organize daemon running when "organize peer ..." commands are run.
    """

    def __init__(self, ctx):
        self.organize = (
            ctx.meta.get('Organize', {}).get('magic_instance')
            or organize_dbus_if_active()
        )

        if ctx.invoked_subcommand is None:
            self.show()

    @DualUse.method(short_help="Show peer information")
    @click.argument('peers', type=str, nargs=-1)
    @click.option(
        '-D',
        '--descriptor',
        is_flag=True,
        help="Print peer descriptor(s) instead of status",
    )
    @click.option('-q', '--qrcode', is_flag=True, help="Print ANSI qrcode(s)")
    @click.option(
        '-a',
        '--all',
        'which',
        flag_value='all',
        help="Show both enabled and disabled peers",
    )
    @click.option(
        '-d',
        '--disabled',
        'which',
        flag_value='disabled',
        help="Show only disabled peers",
    )
    @click.option(
        '-e',
        '--enabled',
        'which',
        flag_value='enabled',
        help="Show only enabled peers",
    )
    def show(self, peers=(), which=None, descriptor=False, qrcode=False):
        """
        Show peer information.

        With no arguments, all enabled peers are shown.

        Peer arguments can be specified as ID, name, or IP, unless options are also
        specified, in which case arguments must (currently) be IDs.
        """

        available = self.organize.peer_ids(which if which else 'enabled')

        queries = (
            available
            if peers == ()
            else (
                [peer for peer in peers if peer in available]
                if which
                else peers
            )
        )

        res = []
        for query in queries:
            if qrcode:
                d = self.organize.peer_descriptor(query)
                desc = Descriptor.parse(d)
                if descriptor:
                    res.append(d)
                else:
                    res.append("{vk} {hostname} {v4a}".format(**desc))
                res.append(desc.qr_code)
            elif descriptor:
                res.append(self.organize.peer_descriptor(query))
            else:
                res.append(self.organize.show_peer(query))

        if output := ("\n" if descriptor else "\n\n").join(res):
            echo_maybepager(output)

    @DualUse.method(short_help="Import peer descriptors", name='import')
    @click.argument('file', type=click.File(), default='-')
    def import_(self, file):
        """
        Import peer descriptors.

        Reads from standard input if a file is not specified.

        Prints the result of processing each descriptor.

        Can consume the output of "vula peer show --descriptor" from another
        system, or the output of "vula discover --no-dbus --interface eth0".
        """
        while True:
            line = file.readline()
            line = line.split(':')[
                -1
            ].strip()  # strip timestamp from discover logs, if present
            if not line:
                break
            line = line.strip()
            res = self.organize.process_descriptor_string(line)
            if res:
                click.echo(yamlrepr_hl.from_yaml(res))
            else:
                click.echo("process_descriptor_string returned None 🤔")

    @DualUse.object(short_help="Add and remove peer addresses")
    @click.pass_context
    class addr(object):
        """
        Modify peer addresses.

        In the future, this might also show addresses, but for now that can be
        done with the "peer show" command.
        """

        def __init__(self, ctx):
            self.organize = (
                ctx.meta.get('Organize', {}).get('magic_instance')
                or organize_dbus_if_active()
            )

        @DualUse.method()
        @click.argument('vk', type=str)
        @click.argument('ip', type=str)
        def add(self, vk, ip):
            """
            Add an address to a peer
            """
            click.echo(Result.from_yaml(self.organize.peer_addr_add(vk, ip)))

        @DualUse.method(name='del')
        @click.argument('vk', type=str)
        @click.argument('ip', type=str)
        def del_(self, vk, ip):
            """
            Delete an address from a peer.

            Note: if the peer re-announces the address, it will be re-added. To
            prevent an address from being (re)enabled, you can set it to
            disabled instead of deleting it. This is currently accomplished
            using a command like "peer set $vk IPv4addrs x.x.x.x false"
            """
            click.echo(Result.from_yaml(self.organize.peer_addr_del(vk, ip)))

    @DualUse.method(short_help="Set arbitrary peer properties")
    @click.argument('vk', type=str, **shell_complete_helper(_ac_get_peer_ids))
    @click.argument('path', type=str, nargs=-1)
    @click.argument('value', type=str)
    def set(self, vk, path, value):
        """
        Modify arbitrary peer properties.

        This is currently the only way to verify peers, enable or disable them,
        and enable or disable IP addresses.

        In the future, this command should perhaps only be available for
        debugging, and the normal user tasks which it currently performs should
        be handled by other commands.

        This command is *not* able to remove keys from dictionaries; for
        removing IP addresses (instead of disabling them with this command) you
        can use the "vula peer addr del" command. This command is able to add new
        IPs, but that is better done with "vula peer addr add".
        """
        res = Result(json.loads(self.organize.set_peer(vk, path, value)))
        click.echo(res)

    @DualUse.method()
    @click.argument('vk', type=str)
    def remove(self, vk):
        """
        Remove a peer.
        """
        res = self.organize.remove_peer(vk)
        res = Result.from_yaml(str(res))
        return res


main = PeerCommands.cli

if __name__ == "__main__":
    import doctest

    print(doctest.testmod())
