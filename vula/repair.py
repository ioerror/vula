from logging import getLogger
from os import geteuid
from sys import stdout, platform

import click

try:
    import pydbus
except:
    pydbus = False
    pass
from .common import organize_dbus_if_active
from .constants import (
    _DATE_FMT,
    _LOG_FMT,
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_DBUS_PATH,
)


@click.command(short_help="Ensure that system is configured correctly")
@click.option(
    '-n',
    '--dry-run',
    is_flag=True,
    help="Print what would be done, without doing it",
)
def main(dry_run):
    """
    This checks if the system is configured correctly, and (re)configures it if
    it isn't.
    """
    log = getLogger()

    organize = organize_dbus_if_active()
    res = organize.sync(dry_run)

    if res:
        print("\n".join(res))
