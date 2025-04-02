import time
from datetime import timedelta
from logging import getLogger
from sys import platform

from platform import node
import json
import click
import pydbus

try:
    from systemd import daemon
except ImportError:
    daemon = None

from click.exceptions import Exit

from .prefs import Prefs
from .peer import Descriptor
from .constants import _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH, _DOMAIN
from .notclick import green, red, yellow


@click.command(short_help="Print status")
@click.option(
    '-s',
    '--only-systemd',
    is_flag=True,
    help="Only print systemd service status",
)
@click.option(
    '-v',
    '--verbose',
    count=True,
    help="Only print systemd service status",
)
def main(only_systemd, verbose):
    """
    Print status of systemd services and system configuration.
    """
    log = getLogger()

    if not platform.startswith("linux"):
        log.error("so far, the status command only works on linux")
        raise Exit(1)

    def printer(status, service):
        status = (
            (lambda x: x)
            if status == 'none'
            else green
            if status in ('active',)
            else (yellow if status in ('inactive', 'activatable') else red)
        )("{:^8}".format(status))
        click.echo("[{}] {}".format(status, service))

    bus = pydbus.SystemBus()

    if daemon is not None and daemon.booted() == 1:
        systemd = bus.get(".systemd1")
        for service in [
            "publish",
            "discover",
            "organize",
            "organize-monolithic",
        ]:
            unit_name = "vula-%s.service" % (service,)
            try:
                unit = bus.get('.systemd1', systemd.GetUnit(unit_name))
            except Exception as ex:
                if 'NoSuchUnit' in str(ex):
                    if 'monolithic' not in unit_name:
                        # hide NoSuchUnit for monolithic service
                        printer('disabled', unit_name)
                else:
                    printer(str(ex), unit_name)
            else:
                printer(
                    unit.ActiveState,
                    "%-35s (%s)"
                    % (
                        unit_name,
                        timedelta(
                            seconds=int(
                                time.time()
                                - unit.StateChangeTimestamp / 1000000
                            )
                        ),
                    ),
                )

    else:
        printer("inactive", "systemd")

    if bus.dbus.NameHasOwner(_ORGANIZE_DBUS_NAME):
        if only_systemd:
            printer("active", _ORGANIZE_DBUS_NAME + ' dbus service')
        else:
            printer(
                "active",
                _ORGANIZE_DBUS_NAME
                + ' dbus service (running repair --dry-run)',
            )
            organize = bus.get(_ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH)
            sync_todo = organize.sync(True)

            enabled_peers = organize.peer_ids('enabled')
            disabled_peers = organize.peer_ids('disabled')

            descs = json.loads(organize.our_latest_descriptors())
            prefs = Prefs(json.loads(organize.get_prefs()))
            if descs:
                descs = {
                    iface: Descriptor.parse(desc)
                    for iface, desc in descs.items()
                }
                if verbose:
                    for iface, desc in descs.items():
                        printer(
                            "active",
                            f"Publishing on {iface}: "
                            + ', '.join(map(str, desc.all_addrs)),
                        )
                else:
                    printer(
                        "active",
                        "Publishing "
                        + ", ".join(
                            f"{len(desc.all_addrs)} IPs on {iface}"
                            for iface, desc in descs.items()
                        ),
                    )
            else:
                printer("none", "no qualifying interfaces")

            if sync_todo:
                printer(
                    "needs repair",
                    "{} enabled peers; {} disabled".format(
                        str(len(enabled_peers)),
                        str(len(disabled_peers)),
                    ),
                )
                for line in sync_todo:
                    printer("needs repair", "[#] %s" % (line,))
            else:
                printer(
                    "active" if len(enabled_peers) else "none",
                    "{} enabled peers correctly configured; "
                    "{} disabled".format(
                        str(len(enabled_peers)),
                        str(len(disabled_peers)),
                    ),
                )
            printer(
                "active",
                f"{node() + _DOMAIN}'s vula ULA is {prefs.primary_ip}",
            )

    elif _ORGANIZE_DBUS_NAME in bus.dbus.ListActivatableNames():
        printer("activatable", _ORGANIZE_DBUS_NAME + ' dbus service')
    else:
        printer("not installed", _ORGANIZE_DBUS_NAME + ' dbus service')
