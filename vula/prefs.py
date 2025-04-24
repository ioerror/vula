from __future__ import annotations

from ipaddress import ip_network

import click
import yaml
from schema import Schema, Use
from ipaddress import ip_address

from .common import (
    DualUse,
    Flexibool,
    organize_dbus_if_active,
    schemattrdict,
    yamlrepr_hl,
)

from .constants import (
    _IPv4_LL,
    _IPv6_LL,
    _IPv6_ULA,
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
            'overwrite_unpinned': Flexibool,  # TODO
            'expire_time': Use(int),  # TODO
            'primary_ip': Use(ip_address),  # TODO
            'record_events': Flexibool,
            'enable_ipv6': Flexibool,
            'enable_ipv4': Flexibool,
        }
    )

    default = dict(
        pin_new_peers=False,
        accept_nonlocal=False,
        auto_repair=True,
        subnets_allowed=[
            str(_IPv6_LL),
            str(_IPv6_ULA),
            str(_IPv4_LL),
            "10.0.0.0/8",
            "192.168.0.0/16",
            "172.16.0.0/12",
        ],
        subnets_forbidden=[],
        iface_prefix_allowed=[
            'en',
            'eth',
            'wl',
            'thunderbolt',
        ],
        local_domains=["local.", "local"],
        ephemeral_mode=False,
        accept_default_route=True,
        record_events=False,
        expire_time=3600,
        overwrite_unpinned=True,
        primary_ip=0,
        enable_ipv6=True,
        enable_ipv4=True,
    )


@DualUse.object(
    invoke_without_command=True,
)
@click.pass_context
class PrefsCommands(object):
    """
    View and modify preferences.
    """

    def __init__(self, ctx):
        self.organize = organize_dbus_if_active()
        if ctx.invoked_subcommand is None:
            click.echo(self.show().strip())

    @DualUse.method()
    def show(self):
        """
        Show preferences.
        """
        res = str(yamlrepr_hl(yaml.safe_load(self.organize.show_prefs())))
        return res

    @DualUse.method()
    @click.argument('pref', type=str)
    @click.argument('value', type=str)
    def set(self, pref, value):
        """
        Set a preference to a value.
        """
        return self.organize.set_pref(pref, value)

    @DualUse.method()
    @click.argument('pref', type=str)
    @click.argument('value', type=str)
    def add(self, pref, value):
        """
        Merge a preference value into a list or dict.
        """
        return self.organize.add_pref(pref, value)

    @DualUse.method()
    @click.argument('pref', type=str)
    @click.argument('value', type=str)
    def remove(self, pref, value):
        """
        Remove a preference value from a list or dict.
        """
        return self.organize.remove_pref(pref, value)


main = PrefsCommands.cli
