import socket
import struct
import time
from typing import Any, Generator, List, Optional, Protocol, Tuple, Union, cast

import click
import ifaddr
from rendez.vous.reunion.__version__ import __version__
from rendez.vous.reunion.session import T1, ReunionSession

from .notclick import DualUse, bold, green, red


class ReunionPeer(Protocol):
    """
    ReunionPeer is a typing helper for ensuring that we have
    """

    t1: T1

    def process_t2(self, t2: bytes) -> Tuple[bytes, bool]: ...
    def process_t3(self, t3: bytes) -> Optional[bytes]: ...


class UDPListeners(object):
    def __init__(
        self,
        bind_addr: str,
        bind_mask: List[str],
        port: int = 0,
        verbose: bool = False,
    ):
        self.session: Optional[ReunionSession] = None
        self.old_session: Optional[ReunionSession] = None
        self.addr_map: dict[Tuple[str, int], ReunionPeer] = {}
        self.old_addr_map: dict[Tuple[str, int], ReunionPeer] = {}
        self.peer_message: Optional[bytes] = None
        self.verbose: bool = verbose
        self.bind_mask: List[str] = bind_mask

        self.bind_addrs: List[str] = []
        self.bind_ifaces: List[str] = []
        # Bind to any vula allowed interfaces with IPv4 addresses
        if bind_addr == "0.0.0.0":
            self.echo(f"{bind_addr=}")
            self.echo(f"{self.bind_mask=}")
            for iface in ifaddr.get_adapters():
                self.echo(f"Candidate iface: {iface.name=}")
                for mask_name in self.bind_mask:
                    self.echo(f"Accept mask: {mask_name=}")
                    if iface.name.startswith(mask_name):
                        self.echo(f"Allowed iface: {iface.name=}")
                        self.bind_ifaces.append(iface.name)
                        for ip in iface.ips:
                            self.echo(f"{ip=}")
                            if ip.is_IPv4:  # Currently only IPv4
                                self.echo(f"Accepting: {str(ip.ip)=}")
                                self.bind_addrs.append(str(ip.ip))
                            else:
                                self.echo(f"Rejecting: {str(ip.ip)=}")
                    else:
                        self.echo(f"Disregarding iface: {iface.name=}")
                        pass
        else:
            # Otherwise bind to the specific IPv4 address passed to reunion
            # This may and can override the interface specific filtering
            self.echo(f"bind_addr: {bind_addr=}")
            self.bind_addrs.append(bind_addr)
        self.echo(f"{self.bind_addrs=}")
        self.echo(f"{self.bind_mask=}")
        self.echo(f"{self.bind_ifaces=}")

        # Create the TX socket(s)
        self.msocks: List[socket.socket]
        self.socks: List[socket.socket]
        self.msocks = []
        self.socks = []
        for bind_addr in self.bind_addrs:
            sock: socket.socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM
            )
            sock.settimeout(0.2)
            ttl: bytes = struct.pack("b", 1)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            self.echo(f"{(bind_addr, port)}")
            sock.bind((bind_addr, port))
            self.socks.append(sock)
        self.echo(f"{self.socks=}")

    def echo(self, msg: str) -> None:
        if self.verbose:
            click.echo(msg)

    def bind_multicast(self, multicast_group: str, port: int) -> None:
        self.echo("Constructing UDPListeners")
        self.echo("Binding multicast")
        ifaces_by_ip: dict[str, Tuple[int, str]] = {
            ip.ip: (a.index, a.name)
            for a in reversed(ifaddr.get_adapters())  # type: ignore
            for ip in a.ips
        }
        for bind_addr in self.bind_addrs:
            if_idx, if_name = ifaces_by_ip.get(
                bind_addr, (socket.INADDR_ANY, "any")
            )
            group: bytes = socket.inet_aton(multicast_group)
            mreq: bytes = struct.pack("4sL", group, if_idx)
            self.echo(
                f"Using {bind_addr} on iface {if_name} ({if_idx}) for multicast to {multicast_group}:{port}"
            )
            msock: socket.socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM
            )
            msock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            msock.bind(("", port))
            msock.settimeout(0.2)
            msock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self.msocks.append(msock)
        self.echo(f"{self.msocks=}")

    def send(
        self, prefix: bytes, message: bytes, dest: Tuple[str, int]
    ) -> None:
        self.echo(f"Sending: {message=}")
        self.echo(f"Sending: {dest=}")
        payload: bytes = prefix + message
        for sock in self.socks:
            sent: int = sock.sendto(payload, dest)
            self.echo(f"{payload, dest=}")
            self.echo(f"{sent=}")
            if sent != len(payload):
                self.echo(
                    f"Tried to send {len(payload)} bytes but only sent {sent}!"
                )
            else:
                self.echo(f"Sent {len(payload)}: {sent}")

    def poll(self) -> Optional[List[bytes]]:
        timeout: bool
        messages: List = []
        for sock in self.socks:
            try:
                data: Optional[bytes]
                addr: Tuple[str, int]
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                timeout = True
                data = None
            if data is not None:
                messages.append(self.process_message(data, addr))
        if len(messages) != 0:
            return messages
        else:
            return None

    def poll_multicast(self) -> Optional[List[bytes]]:
        timeout: bool
        messages: List = []
        for msock in self.msocks:
            try:
                data: Optional[bytes]
                addr: Tuple[str, int]
                data, addr = msock.recvfrom(1024)
            except socket.timeout:
                timeout = True
                data = None
            if data is not None and data.startswith(b"t1"):
                messages.append(self.process_message(data, addr))
        if len(messages) != 0:
            return messages
        else:
            return None

    def process_message(
        self, data: bytes, addr: Tuple[str, int]
    ) -> Optional[bytes]:
        if self.session is None:
            self.echo("No session established")
            return None

        # Decode the first 5 bytes to avoid str-bytes formatting issues.
        self.echo(
            f"Received {len(data)} byte message {data[:5].hex()} from {addr[0]}:addr[1]"
        )
        peer: Optional[ReunionPeer] = self.addr_map.get(addr)
        if not peer:
            peer = self.old_addr_map.get(addr)
            if peer and data[:2] != b"t1":
                self.echo(
                    f"!!! Received {data[:4].hex()!r} for {peer.t1!r} from previous epoch"
                )
        if data.startswith(b"t1"):
            t1: T1 = T1(data[3:])
            if t1.id in self.session.peers:
                self.echo(f"Ignoring replay of {t1!r} from {addr}")
                return None
            elif t1.id == self.session.t1.id:
                self.echo(f"Ignoring our own {t1!r} from {addr}")
                return None
            if data[2:3] == b"r":
                self.echo(f"Received t1r {t1!r} from {addr}")
            else:
                self.echo(f"Received t1_ {t1!r} from {addr} {data[:5].hex()}")
                self.send(b"t1r", self.session.t1, addr)
            t2_resp: bytes = self.session.process_t1(t1)
            self.send(b"t2", t2_resp, addr)
            self.addr_map[addr] = self.session.peers[t1.id]

        elif data.startswith(b"t2"):
            if not peer:
                self.echo(f"Ignoring t2 message from unknown peer {addr}")
                return None
            t2: bytes = data[2:]
            assert peer is not None
            t3: bytes
            is_dummy: bool
            t3, is_dummy = peer.process_t2(t2)
            if is_dummy:
                self.echo(
                    f"Decryption of t2 from {addr} failed; sending dummy"
                )
            else:
                self.echo(
                    f"Successful decryption of t2 from {addr}; sending reveal"
                )
            self.send(b"t3", t3, addr)

        elif data.startswith(b"t3"):
            if not peer:
                self.echo(f"Ignoring t3 message from unknown peer: {addr}")
                return None
            t3_msg: bytes = data[2:]
            self.echo(f"Received t3 {peer.t1!r} from {addr}")
            assert peer is not None
            res: bytes = self.process_result(
                peer.process_t3(t3_msg), addr, peer
            )
            self.echo(f"Result for t3: {res.hex()}")
            self.peer_message = res
        else:
            self.echo(
                f"Peer {addr} sent us something weird: {data[:50].hex()}"
            )
        return None

    def process_result(
        self,
        payload: Optional[bytes],
        addr: Tuple[str, int],
        peer: ReunionPeer,
    ) -> bytes:
        if payload is not None:
            self.echo(f"Decrypted message from {peer.t1!r} on {addr}")
            return payload
        else:
            return b""

    def new_session(self, passphrase: bytes, message: bytes) -> None:
        if self.verbose:
            self.echo("Creating new reunion session... ")
        started: float = time.time()
        self.old_session, self.session = self.session, ReunionSession.create(
            passphrase, message
        )
        # Assert that we got a valid session so mypy knows session is not None.
        assert self.session is not None
        if self.verbose:
            t: float = time.time() - started
            self.echo(f"OK: creating {self.session.t1!r} took {t:.1f} seconds")
        self.old_addr_map, self.addr_map = self.addr_map, {}


def reunion_multicast_run_verify(
    passphrase: str,
    message: bytes,
    interval: int,
    multicast_group: str,
    port: int,
    reveal_once: bool,
    bind_addr: str,
    bind_mask: List[str],
    timeout: int,
    hostname: str,
    verbose: bool,
) -> bytes:
    if reveal_once != True:
        raise click.ClickException(
            "REUNION multi-reveal support is currently unavailable"
        )
    passphrase_b: bytes = passphrase.encode()
    udp: UDPListeners = UDPListeners(bind_addr, bind_mask, 0, verbose)
    udp.bind_multicast(multicast_group, port)

    started: Optional[float] = None
    msg: bool = False
    peer_payload: Optional[bytes] = None
    first_started: float = time.time()
    while not msg:
        if started is None or time.time() - started > interval:
            started = time.time()
            udp.new_session(passphrase_b, message)
            assert udp.session is not None
            udp.send(b"t1_", udp.session.t1, (multicast_group, port))
        elif time.time() - first_started > timeout:
            break
        udp.poll()
        udp.poll_multicast()
        if udp.peer_message is not None:
            msg = True
            peer_payload = udp.peer_message
            if len(peer_payload) != 32:
                click.echo(red("Hashed peer VK length incorrect"))
                raise click.ClickException("Verification failed")
            else:
                break
    if peer_payload is not None:
        return peer_payload
    else:
        raise click.ClickException("REUNION timeout reached")
