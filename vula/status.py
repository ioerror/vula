from logging import getLogger
from os import geteuid
from sys import stdout, platform
import time
from datetime import timedelta
import click
from click.exceptions import Exit
import yaml
from gi.repository import GLib

import pydbus

try:
    from systemd import daemon
except ImportError:
    daemon = None

from click.exceptions import Exit
from .common import bp, yamlrepr_hl
from .click import green, red, yellow, echo_maybepager

from .constants import (
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_DBUS_PATH,
)


@click.command(short_help="Print status")
@click.option(
    '-s',
    '--only-systemd',
    is_flag=True,
    help="Only print systemd service status",
)
def main(only_systemd):
    """
    Print status of systemd services and system configuration
    """
    log = getLogger()

    if not platform.startswith("linux"):
        log.error("so far, the status command only works on linux")
        raise Exit(1)

    def printer(status, service):
        status = "{:^8}".format(status)
        status = (
            green
            if status.strip() in ('active',)
            else yellow
            if status.strip() in ('inactive', 'activatable')
            else red
        )(status)
        click.echo("[{}] {}".format(status, service))

    bus = pydbus.SystemBus()

    if daemon is not None and daemon.booted() == 1:
        systemd = bus.get(".systemd1")
        all_units = {str(u[0]): u for u in systemd.ListUnits()}
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
            if sync_todo:
                printer(
                    "needs repair",
                    "{} enabled peers; {} disabled".format(
                        str(len(organize.peer_ids('enabled'))),
                        str(len(organize.peer_ids('disabled'))),
                    ),
                )
                for line in sync_todo:
                    printer("needs repair", "[#] %s" % (line,))
            else:
                printer(
                    "active",
                    "{} enabled peers correctly configured; {} disabled".format(
                        str(len(organize.peer_ids('enabled'))),
                        str(len(organize.peer_ids('disabled'))),
                    ),
                )

    elif _ORGANIZE_DBUS_NAME in bus.dbus.ListActivatableNames():
        printer("activatable", _ORGANIZE_DBUS_NAME + ' dbus service')
    else:
        printer("not installed", _ORGANIZE_DBUS_NAME + ' dbus service')
