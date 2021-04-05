"""
 vula-publish is a program that announces a WireGuard mDNS service as
 informed by Organize over dbus or as controlled by organize in monolith mode.
"""

from logging import Logger, getLogger
from platform import node

import click
from zeroconf import ServiceInfo, Zeroconf

import pydbus
from gi.repository import GLib
from ipaddress import ip_address

from .constants import (
    _LABEL,
    _PUBLISH_DBUS_NAME,
)
from .common import comma_separated_IPs


class Publish(object):

    dbus = '''
    <node>
      <interface name='local.vula.publish1.Listen'>
        <method name='listen'>
          <arg type='a{sa{ss}}' name='new_announcements' direction='in'/>
        </method>
      </interface>
    </node>
    '''

    def __init__(self):

        self.log: Logger = getLogger()
        self.zeroconfs = {}

    def listen(self, new_announcements):
        # First we remove all old zeroconf listeners that are not in our new instructions
        for ip, zc in list(self.zeroconfs.items()):
            if ip not in new_announcements:
                self.log.info("Removing old service announcement for %r", ip)
                zc.close()
                del self.zeroconfs[ip]
        # Now we add a zeroconf listener for each new IP and ServiceInfo if it
        # is not already existing, else we update the old zc object with the
        # new desc
        for ip_addr, desc in new_announcements.items():
            self.log.debug(
                "Starting mDNS service announcement for %r", ip_addr
            )
            name: str = node() + "." + _LABEL
            service_info: ServiceInfo = ServiceInfo(
                _LABEL,
                name=name,
                addresses=[
                    ip_address(ip).packed for ip in desc['addrs'].split(',')
                ],
                port=int(desc['port']),
                properties=desc,
                server=desc['hostname'],
            )
            zeroconf = self.zeroconfs.get(ip_addr)
            if zeroconf:
                # Do update dance
                self.log.debug("Updating vula service: %s", service_info)
                zeroconf.update_service(service_info)
                self.log.debug("Updating vula service.")

            else:
                zeroconf = self.zeroconfs[ip_addr] = Zeroconf(
                    interfaces=list(map(str, comma_separated_IPs(ip_addr)))
                )
                self.log.debug("Registering vula service: %s", service_info)
                zeroconf.register_service(service_info)
                self.log.debug("Registered vula service.")

    @classmethod
    def daemon(cls):
        """
        This method implements the non-monolithic daemon mode where we run
        Publish in its own process (as we deploy on GNU/systemd).
        """
        loop = GLib.MainLoop()
        publish = cls()
        publish.log.debug("Debug level logging enabled")
        pydbus.SystemBus().publish(_PUBLISH_DBUS_NAME, publish)
        publish.log.debug("dbus enabled")
        loop.run()


@click.command()
def main(**kwargs):
    Publish.daemon(**kwargs)


if __name__ == "__main__":
    main()
