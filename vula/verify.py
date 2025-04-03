"""
 vula-verify is a stateless program that generates and reads QR codes to
 verify a peer or a set of vula peers.  This program's output is intended to
 be fed into the vula-organize daemon. It should authenticate an already
 known peer or peers and sets a bit to keep state that it has verified them.
 The QR code also includes a PSK and later will use CTIDH to automatically set
 a PSK on a pair-wise basis.

 The output of this program may be written to a pipe, a log file, a unix
 socket, or any other place. It should run with the lowest possible privileges
 possible. The output is not filtered and so adversaries may attempt to inject
 unreasonable data. Care should be taken that the data should only be used
 after it has been verified.
"""

import hashlib
import json
import sys

from base64 import b64decode
import click
from typing import Any, Callable, Generator, List, Optional, Tuple, Union
from types import ModuleType
import pydbus
import yaml
from click.exceptions import Exit
from gi.repository import GLib

try:
    cv2: Optional[ModuleType]
    import cv
except ImportError:
    cv2 = None

try:
    zbar: Optional[ModuleType]
    from pyzbar.pyzbar import decode
except ImportError:
    zbar = None

try:
    qrcode: Optional[ModuleType]
    import qrcode
except ImportError:
    qrcode = None

from .common import escape_ansi
from .constants import _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
from .engine import Result
from .notclick import DualUse, bold, green, red
from .peer import Descriptor
from .verify_audio import VerifyAudio
from .verify_reunion import reunion_multicast_run_verify


@DualUse.object(
    short_help="Verify and share peer verification information",
    invoke_without_command=False,
)
@click.pass_context
class VerifyCommands(object):
    cli: Callable[[], None]

    def __init__(self, ctx):
        organize = ctx.meta.get('Organize', {}).get('magic_instance')

        if not organize:
            bus = pydbus.SystemBus()
            organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)

        self.organize = organize
        self.my_descriptors = {
            ip: Descriptor(d)
            for ip, d in json.loads(
                self.organize.our_latest_descriptors()
            ).items()
        }
        (self.vk,) = set(d.vk for d in self.my_descriptors.values())
        self.ifaces_mask: List[str] = self.organize.prefs[
            'iface_prefix_allowed'
        ]

    def _lookup_peer_vk_hostname(self, hostname: str) -> Tuple[str, bytes]:
        try:
            # Lookup hostname and hash it
            peer_vk_b64: str = self.organize.get_vk_by_name(hostname)
            peer_vk: bytes = b64decode(peer_vk_b64)
            peer_vk_hashed: bytes = hashlib.sha256(peer_vk).digest()
        except GLib.Error:
            raise click.ClickException(
                f"hostname {hostname} unknown, "
                f"can only verify previously discovered hosts"
            )
        return peer_vk_b64, peer_vk_hashed

    @DualUse.method()
    def my_vk(self):
        click.echo(green(bold("Your VK is: ")) + str(self.vk))
        qr = qrcode.QRCode()
        qr.add_data(data="local.vula:vk:" + str(self.vk))
        qr.print_tty()

    @DualUse.method()
    def my_descriptor(self):
        for ip, desc in self.my_descriptors.items():
            click.echo(green(bold("Descriptor for {}: ".format(ip))))
            qr = qrcode.QRCode()
            qr.add_data(data="local.vula:desc:" + str(desc))
            qr.print_tty()
            click.echo(repr(str(desc)))

    @DualUse.method()
    @click.argument('name', type=str)
    def against(self, name):
        # take name vk and vk (self), hash with sha256
        pass

    @DualUse.method()
    @click.option('-w', '--width', default=640, show_default=True)
    @click.option('-h', '--height', default=480, show_default=True)
    @click.option('-c', '--camera', default=0, show_default=True)
    @click.option(
        '-d', '--debug', default=False, is_flag=True, show_default=True
    )
    @click.argument('hostname', type=str, required=True)
    def scan(self, width, height, camera, hostname, debug):
        """
        We expect a string object that roughly looks like the following three
        things:


            local.vula:desc:<descriptor base64 representation>
            local.vula:vk:<vk base64 representation>
            local.vula:aead:<aead ciphertext base64 representation>

        The first part of the string is conformant to RFC 1738, Section 2.1.
        which describes "The main parts of URLs".
        """
        res = None
        done = False
        data = None
        v = cv2.VideoCapture(camera, cv2.CAP_V4L)
        v.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        v.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        while v.isOpened():
            ret, img = v.read()
            if not ret:
                break
            cv2.imshow("scan vula qrcode", img)
            k = cv2.waitKey(1)
            if k == ord('q'):
                break
            res = decode(img)
            if res:
                if debug:
                    click.echo(res)
                for result in res:
                    if result.type == 'QRCODE':
                        if result.data.decode('utf-8').startswith(
                            'local.vula:'
                        ):
                            data = result.data.decode('utf-8')
                            done = True
                            break
            if done:
                break
        if not data:
            exit(1)
        data = data.split(':', 1)[1]
        sub_type, data = data.split(':', 1)
        if sub_type == "desc":
            res = self.organize.process_descriptor_string(data)
            res = Result(yaml.safe_load(res))
            click.echo(res)
        elif sub_type == "vk":
            vk = self.organize.get_vk_by_name(hostname)
            if vk == data:
                res = self.organize.verify_and_pin_peer(vk, hostname)
                res = Result(yaml.safe_load(res))
                click.echo(res)
                if res.error is not None:
                    raise Exception(res.error)
            else:
                click.echo("keys are for the wrong DeLorean")
                raise Exit(1)
        else:
            click.echo("unknown qrcode subtype")
            raise Exit(1)
        if res.error is not None:
            click.echo(res)
            raise Exit(1)
        else:
            if debug:
                click.echo(res)
            raise Exit(0)

    @DualUse.method()
    @click.option(
        '-v', '--verbose', default=False, is_flag=True, show_default=True
    )
    def speak(self, verbose):
        vk = str(self.vk)
        if verbose:
            click.echo(f"Sending vk: {vk}")
        VerifyAudio(verbose).send_verification_key(vk)
        if verbose:
            click.echo("Done speaking.")

    @DualUse.method()
    @click.argument('hostname', type=str, required=True)
    @click.option(
        '-v',
        '--verbose',
        default=False,
        is_flag=True,
        show_default=True,
        type=bool,
    )
    def listen(self, hostname: str, verbose: bool):
        try:
            known_vk = self.organize.get_vk_by_name(hostname)
        except GLib.Error:
            click.echo(
                f"hostname {hostname} unknown, "
                f"can only verify previously discovered hosts"
            )
            sys.exit(6)
        click.echo(green(bold('Listening ... ')) + 'Press Ctrl+C to stop')
        received_vk = VerifyAudio(verbose).receive_verification_key()
        if received_vk is not None:
            sanitized_vk: str = escape_ansi(received_vk)
            if sanitized_vk != received_vk:
                click.echo(
                    "The received verification key had to be sanitized, "
                    "this is a possible injection attack!"
                )
                raise Exit(1)
            if verbose:
                click.echo(f"Received VK: {sanitized_vk}")
            if (
                hashlib.sha256(known_vk.encode('utf-8')).hexdigest()
                == received_vk
            ):
                res = self.organize.verify_and_pin_peer(known_vk, hostname)
                res = Result(yaml.safe_load(res))
                click.echo(res)
                if res.error is not None:
                    raise Exception(res.error)
            else:
                click.echo(
                    red(
                        bold(
                            f"The received vk: {sanitized_vk}"
                            f" and known vk: {known_vk} "
                            f"of hostname {hostname} do not match."
                        )
                    )
                )
                if verbose:
                    print("keys are for the wrong DeLorean")
                raise Exit(1)

    @DualUse.method()  # type: ignore
    @click.argument("hostname", required=True, type=str)
    @click.option(
        "--multicast-group",
        default="224.3.29.71",
        show_default=True,
        type=str,
        help="Multicast group",
    )
    @click.option(
        "--multicast-port",
        default=9005,
        show_default=True,
        type=int,
        help="Multicast listener port",
    )
    @click.option(
        "--bind-addr",
        default="0.0.0.0",
        show_default=True,
        type=str,
        help="By default we bind to all IPv4 addresses where vula is operating",
    )
    @click.option(
        "--bind-mask",
        default=["all"],
        multiple=True,
        show_default=True,
        type=str,
        help="vula's iface_prefix_allowed is the default interface mask list",
    )
    @click.option(
        "--reveal-once",
        is_flag=True,
        default=True,
        type=bool,
        help="Only reveal our VK to the first peer with the correct passphrase",
    )
    @click.option(
        "--passphrase",
        prompt=True,
        hide_input=True,
        type=str,
        help="The passphrase for the REUNION session",
    )
    @click.option(
        "--interval",
        "-I",
        default=15,
        show_default=True,
        type=int,
        help="Interval at which to start new sessions",
    )
    @click.option(
        "--timeout",
        "-t",
        default=60,
        show_default=True,
        type=int,
        help="Timeout",
    )
    @click.option(
        "--verbose",
        is_flag=True,
        default=False,
        type=bool,
        help="Verbose output",
    )
    def reunion(self, **kw: Any) -> int:
        """
        Verify a host using the rendez.vous.reunion.multicast REUNION API.

        The hashed *vk* for the host is shared under the *passphrase* for the
        REUNION session. We expect to receive the hashed *vk* of the peer
        *hostname*.

        If the received *vk* hash matches the expected value for the peer
        hostname's hashed vk, the host's vk is marked as verified and then the
        *vk* for the hostname is pinned.

        By default, we bind the multicast REUNION protocol to each interface
        that is in the list of allowed vula interfaces. The REUNION protocol
        runs every *interval* until success or until the *timeout* threshold
        has been reached. To share your *vk* with more than one party under the
        same *passphrase*, the *reveal-once* option may be set to False.
        """
        hostname: str = kw['hostname']
        verbose: bool = kw['verbose']
        if kw['bind_mask'] == "all" or kw['bind_addr'] == "0.0.0.0":
            kw['bind_mask'] = self.ifaces_mask
        elif kw['bind_addr'] != "0.0.0.0":
            kw['bind_mask'] = ()
        click.echo(green(bold(f"Verifying {hostname} with reunion")))
        if verbose:
            click.echo("Press Ctrl+C to stop")
        expected_peer_vk: str
        expected_peer_vk_hashed: bytes
        (
            expected_peer_vk,
            expected_peer_vk_hashed,
        ) = self._lookup_peer_vk_hostname(hostname)
        message: bytes = hashlib.sha256(bytes(self.vk)).digest()
        kw['message'] = message
        try:
            hashed_peer_vk: Optional[bytes] = reunion_multicast_run_verify(
                **kw
            )
        except click.ClickException:
            hashed_peer_vk = None
        if hashed_peer_vk is None:
            click.echo(
                red(bold("No valid response received. Verification failed."))
            )
            raise click.ClickException("Verification failed")
        if len(hashed_peer_vk) != 32:
            click.echo(
                red(
                    bold(
                        "Invalid length of peer vk received. Verification failed."
                    )
                )
            )
        if hashed_peer_vk == expected_peer_vk_hashed:
            res: str = self.organize.verify_and_pin_peer(
                expected_peer_vk, hostname
            )
            yamlres: Result = Result(yaml.safe_load(res))
            if yamlres is not None and yamlres.ok:
                if verbose:
                    click.echo(yamlres)
                click.echo(
                    green(
                        bold(
                            f"Verification succeeded: {hostname} is verified and pinned."
                        )
                    )
                )
                exit(0)
            else:
                raise Exception(yamlres.error)
        else:
            click.echo(red(bold(f"The received vk and does not match.")))
            if verbose:
                click.echo(f"{hashed_peer_vk=}")
                click.echo(f"{expected_peer_vk_hashed=}")
                click.echo(f"{expected_peer_vk=}")
                click.echo("keys are for the wrong DeLorean")
            raise Exit(1)


main = VerifyCommands.cli
if __name__ == "__main__":
    main()
