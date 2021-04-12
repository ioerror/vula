from __future__ import annotations
from logging import Logger, getLogger
import time

import click
import pydbus
import yaml
from schema import Schema, Use, Optional
from ipaddress import ip_network

from .click import OrderedGroup
from .common import (
    schemattrdict,
    yamlrepr_hl,
    Flexibool,
    organize_dbus_if_active,
    DualUse,
)
from .constants import (
    _DATE_FMT,
    _LOG_FMT,
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_DBUS_PATH,
)


class Prefs(yamlrepr_hl, schemattrdict):

    schema = Schema(
        {
            'pin_new_peers': Flexibool,
            'auto_repair': Flexibool,
            'subnets_allowed': [Use(ip_network)],
            'subnets_forbidden': [Use(ip_network)],
            'iface_prefix_allowed': [str],
            'accept_nonlocal': Flexibool,
            'local_domains': [str],
            'ephemeral_mode': Flexibool,
            'accept_default_route': Flexibool,
            Optional('overwrite_unpinned'): Flexibool,  # TODO
            Optional('expire_time'): int,  # TODO
            'record_events': Flexibool,
        }
    )

    default = dict(
        pin_new_peers=False,
        accept_nonlocal=False,
        auto_repair=True,
        subnets_allowed=[
            "10.0.0.0/8",
            "192.168.0.0/16",
            "172.16.0.0/12",
            "169.254.0.0/16",
        ],
        subnets_forbidden=[],
        iface_prefix_allowed=[
            'en',
            'eth',
            'wl',
            'thunderbolt',
            # 'mpqemubr0',
        ],
        local_domains=["local."],
        ephemeral_mode=False,
        accept_default_route=True,
        record_events=False,
        expire_time=3600,
        overwrite_unpinned=True,
    )


@DualUse.object(invoke_without_command=True,)
@click.pass_context
class PrefsCommands(object):
    """
    View and modify preferences
    """

    def __init__(self, ctx):
        self.organize = organize_dbus_if_active()
        if ctx.invoked_subcommand is None:
            click.echo(self.show().strip())

    @DualUse.method()
    def show(self):
        """
        Show preferences
        """
        res = str(yamlrepr_hl(yaml.safe_load(self.organize.show_prefs())))
        return res

    @DualUse.method()
    @click.argument('pref', type=str)
    @click.argument('value', type=str)
    def set(self, pref, value):
        """
        Set a preference to a value
        """
        return self.organize.set_pref(pref, value)

    @DualUse.method()
    @click.argument('pref', type=str)
    @click.argument('value', type=str)
    def add(self, pref, value):
        """
        Merge a preference value into a list or dict
        """
        return self.organize.add_pref(pref, value)

    @DualUse.method()
    @click.argument('pref', type=str)
    @click.argument('value', type=str)
    def remove(self, pref, value):
        """
        Remove a preference value from a list or dict
        """
        return self.organize.remove_pref(pref, value)


main = PrefsCommands.cli
