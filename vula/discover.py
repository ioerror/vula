"""
 vula-discover is a stateless program that prints each WireGuard mDNS
 service and formats the service parameters into a single easy to parse line.
 This program's output is intended to be fed into a daemon that configures
 wireguard peers discovered by vula to configure the local vula
 interface.

 The output of this program may be written to a pipe, a log file, a unix
 socket, the vula-organize dbus Interface for processing descriptors, or any
 other place. It should run with the lowest possible privileges possible. The
 output is not filtered and so adversaries may attempt to inject unreasonable
 hosts such as `127.0.0.1` or other addresses. Care should be taken that only
 addresses for the local network segment are used as WireGuard peers.
"""

from ipaddress import ip_address as ip_addr_parser
from logging import Logger, getLogger
from typing import Optional

import click
import pydbus
from click.exceptions import Exit
from gi.repository import GLib
from pyroute2 import IPRoute
from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

from .constants import (
    _DISCOVER_DBUS_NAME,
    _LABEL,
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_DBUS_PATH,
)
from .peer import Descriptor


class WireGuardServiceListener(ServiceListener):
    """
    *WireGuardServiceListener* is for use with *zeroconf's* *ServiceBrowser*.
    The key=value pairs conform to
    https://tools.ietf.org/html/rfc6763#section-6.4
    """

    def __init__(self, callback):
        super(WireGuardServiceListener, self).__init__()
        self.log: Logger = getLogger()
        self.callback = callback

    def remove_service(
        self, zeroconf: Zeroconf, s_type: str, name: str
    ) -> None:
        """
        *remove_service* does nothing.
        """
        self.log.debug(
            "remove_service called: %s, %s, %s", zeroconf, s_type, name
        )

    def add_service(self, zeroconf: Zeroconf, s_type: str, name: str) -> None:
        """
        When zeroconf discovers a new WireGuard service it calls *add_service*
        which produces a peer descriptor on *stdout*.
        """
        # Typing note:
        # 'Any' works here and while 'Optional[ServiceInfo]' should, it does
        # not unless mypy is called with --no-strict-optional like so:
        #
        #   mypy --ignore-missing-imports  --no-strict-optional discover.py
        info: Optional[ServiceInfo] = zeroconf.get_service_info(s_type, name)
        if info is None:
            return
        data = {k.decode(): v.decode() for k, v in info.properties.items()}

        try:
            desc = Descriptor(data)
        except Exception as ex:
            self.log.debug(
                "discover dropped invalid descriptor: %r (%r)" % (data, ex)
            )
            return

        self.callback(desc)

    def update_service(self, *a, **kw):
        return self.add_service(*a, **kw)


class Discover(object):

    dbus = '''
    <node>
      <interface name='local.vula.discover1.Listen'>
        <method name='listen'>
          <arg type='as' name='ip_addrs' direction='in'/>
        </method>
      </interface>
    </node>
    '''

    def __init__(self):

        self.callbacks = []
        self.browsers = {}
        self.log: Logger = getLogger()

    def callback(self, value):
        for callback in self.callbacks:
            callback(value)

    def listen_on_ip_or_if(self, ip_address, interface):

        """
        Deprecated.

        This is for the cli to accept interface names.
        """

        if interface and ip_address:
            self.log.info("Must pick interface or IP address")
            raise Exit(1)

        ip_addr = None

        if ip_address:
            try:
                ip_addr = str(ip_addr_parser(ip_address))
            except:  # noqa: E722
                self.log.info("Invalid IP address argument")
                raise Exit(3)
            ip_addr: str = ip_address
        elif interface:
            with IPRoute() as ipr:
                index = ipr.link_lookup(ifname=interface)[0]
                a = ipr.get_addr(match=lambda x: x['index'] == index)
                ip_addr: str = dict(a[0]['attrs'])['IFA_ADDRESS']

        if ip_addr:
            self.listen([ip_addr])

    def listen(self, ip_addrs):
        for ip_addr in ip_addrs:
            if ip_addr in self.browsers:
                self.log.info("Not launching a second browser for %r", ip_addr)
                continue
            zeroconf: Zeroconf = Zeroconf(interfaces=[ip_addr])
            self.log.debug("Starting ServiceBrowser for %r", ip_addr)
            browser: ServiceBrowser = ServiceBrowser(
                zeroconf, _LABEL, WireGuardServiceListener(self.callback)
            )
            self.browsers[ip_addr] = (zeroconf, browser)
        for old_ip in list(self.browsers):
            if old_ip not in ip_addrs:
                self.log.info(
                    "Removing old service browser for %r (new ip_addrs=%r)",
                    old_ip,
                    ip_addrs,
                )
                self.browsers[old_ip][1].cancel()
                self.browsers[old_ip][0].close()
                del self.browsers[old_ip]

    def shutdown(self):
        for ip, browser in list(self.browsers.items()):
            del self.browsers[ip]
            browser.cancel()

    def is_alive(self):
        return any(browser.is_alive() for browser in self.browsers.values())

    @classmethod
    def daemon(cls, use_dbus, ip_address, interface):

        """
        This method implements the non-monolithic daemon mode where we run
        Discover in its own process (as we deploy on GNU/systemd).
        """

        loop = GLib.MainLoop()

        discover = cls()

        discover.callbacks.append(lambda d: discover.log.info("%s", d))

        if use_dbus:
            discover.log.debug("dbus enabled")
            system_bus = pydbus.SystemBus()
            process = system_bus.get(
                _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
            ).process_descriptor_string
            discover.callbacks.append(lambda d: process(str(d)))
            system_bus.publish(_DISCOVER_DBUS_NAME, discover)

        discover.listen_on_ip_or_if(ip_address, interface)

        loop.run()


# FIXME: should we shutdown zeroconf objects upon glib shutdown? probably.
#        try:
#            while True:
#                sleep(1)
#        except KeyboardInterrupt:
#            pass
#        finally:
#            discover.shutdown()
#        return 0


@click.command(short_help="Layer 3 mDNS discovery daemon")
@click.option(
    "-d",
    "--dbus/--no-dbus",
    'use_dbus',
    default=True,
    is_flag=True,
    help="use dbus for IPC",
)
@click.option(
    "-I",
    "--ip-address",
    type=str,
    help="bind this IP address instead of automatically choosing which IP "
    "to bind",
)
@click.option(
    #    "-i",
    "--interface",
    type=str,
    help="bind to the primary IP address for the given interface, "
    "automatically choosing which IP to announce",
)
def main(**kwargs):
    Discover.daemon(**kwargs)


if __name__ == "__main__":
    main()
