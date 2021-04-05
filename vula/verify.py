"""
 vula-verify is a stateless program that generates and reads QR codes to
 verify a peer or a set of vula peers.  This program's output is intended to
 be fed into the vula-organize daemon. It should authenticate an already
 known peer or peers and sets a bit to keep state that it has verified them.
 The QR code also includes a PSK and later will use CSIDH to automatically set
 a PSK on a pair-wise basis.

 The output of this program may be written to a pipe, a log file, a unix
 socket, or any other place. It should run with the lowest possible privileges
 possible. The output is not filtered and so adversaries may attempt to inject
 unreasonable data. Care should be taken that the data should only be used
 after it has been verified.
"""

from logging import INFO, DEBUG, Logger, basicConfig, getLogger
from sys import stdout

try:
    import cv2
    from pyzbar.pyzbar import decode
except ImportError:
    zbar = None
    cv2 = None
    decode = None

try:
    import qrcode
except ImportError:
    qrcode = None

import yaml
import click
from click.exceptions import Exit
import pydbus
from time import sleep

from .constants import (
    _DATE_FMT,
    _LABEL,
    _LOG_FMT,
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_DBUS_PATH,
)
from .click import DualUse, green, bold
from .peer import Descriptor
from .engine import Result


@DualUse.object(
    short_help="Verify and share peer verification information",
    invoke_without_command=False,
)
@click.pass_context
class VerifyCommands(object):
    def __init__(self, ctx):
        organize = ctx.meta.get('Organize', {}).get('magic_instance')

        if not organize:
            bus = pydbus.SystemBus()
            organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)

        self.organize = organize
        with open(_WG_PUBLISH_BASEDIR + 'descriptor') as fhandle:
            self.raw_descriptor = fhandle.read()
        self.descriptor = Descriptor.parse(self.raw_descriptor)
        self.vk = self.descriptor.vk
        self.qr = qrcode.QRCode()

    @DualUse.method()
    def my_vk(self):
        self.qr.add_data(data="local.vula:vk:" + str(self.vk))
        click.echo(green(bold("Your VK is: ")) + str(self.vk))
        self.qr.print_ascii()

    @DualUse.method()
    def my_descriptor(self):
        self.qr.add_data(data="local.vula:desc:" + self.raw_descriptor)
        click.echo(green(bold("Your latest descriptor is: ")))
        self.qr.print_ascii()

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
        We expect a string object that roughly looks like the following three things:


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
        elif sub_type == "vk":
            vk = self.organize.get_vk_by_name(hostname)
            if vk == data:
                res = self.organize.verify_and_pin_peer(vk, hostname)
                res = Result(yaml.safe_load(res))
                if res.error != "None":
                    click.echo(res)
                    raise Exception(res.error)
            else:
                click.echo("keys are for the wrong DeLorean")
                raise Exit(1)
        else:
            click.echo("unknown qrcode subtype")
            raise Exit(1)
        if res.error != "None":
            click.echo(res)
            raise Exit(1)
        else:
            click.echo(res)
            raise Exit(0)


main = VerifyCommands.cli
if __name__ == "__main__":
    main()
