---
title: "Status"
date: 2021-08-04T18:11:21+02:00
draft: false
---

### What works

* Automatically adding and removing peers and their routes when the system
  binds and unbinds IPs

* Automatically adding and removing the default route over the vula interface
  depending on if the system gateway coincides with a peer's IP.

* Keeping pinned peers and routes (including the gateway, when applicable)
  active after network state changes.

* Releasing the route via a pinned gateway peer via the `vula release-gateway`
  command, when the user is intentionally roaming away from a network where a
  pinned peer was the gateway.

* Editing peers and preferences using subcommands of `vula peer` and `vula
  prefs`.

### Known issues

Numerous in-progress known issues are documented in
[TODO.md](https://codeberg.org/vula/vula/src/branch/main/TODO.md), but
the most important issues to be aware of when using vula today are these:

* IPv6 support is only partially implemented. At this time, IPv6 traffic is not
  automatically protected. This includes internet-destined IPv6 traffic when
  the gateway is running `vula`. It is likely that there are currently ways
  that an attacker could use IPv6 to circumvent vula's protection of IPv4
  traffic against active attacks, so, for those protections to be strong you
  should currently disable IPv6 on the system completely. Vula's IPv6 support
  is improving, however, and we plan to provide strong protections against
  active attackers while using IPv6 in the near future.

* Coexistence with other usage of another VPN with a default route set over it
  is currently a bit complicated. VPNs other than wireguard have not been
  adequately investigated, but other wireguard configurations can be made to
  cooexist with vula by following the steps described in next paragraph.

  Activating a WireGuard interface using a typical `wg-quick` configuration
  after `vula` is already running will cause `wg-quick` to insert its policy
  routing rules with a lower `pref` value (meaning, a higher priority) which
  will circumvent vula's rule and prevent traffic to vula peers from being
  protected. This can be worked around by editing the other connection's
  `wg-quick` config to set `Table = off` and to have `PostUp` and `PostDown`
  lines to perform all of the steps `wg-quick` normally performs, but with the
  addition of `pref` arguments in the `ip rule add` commands specifying `pref`
  values greater than vula's (666). Additionally, the `wg-quick`-managed
  interface should have its `Mtu` set it 1340, to allow for the overhead of
  running it over a vula gateway.  Lastly, for inbound packets from the other
  VPN arriving on the vula interface to be received by the wireguard listener,
  it is necessary to run `sysctl -w net.ipv4.conf.all.rp_filter=0` and `sysctl
  -w net.ipv4.conf.vula.rp_filter=0` to disable the reverse-path filter for the
  vula interface. The documentation for `rp_filter` is
[here](https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/Documentation/networking/ip-sysctl.rst?h=v6.1#n1555). This should be handled automatically in the future.

* The `vula verify` subcommands, including QR code scanning, have bitrotted and
  are currently non-functional. Peers can be marked as `pinned` and `verified`
  using the `vula peer set` command for now.

### Troubleshooting

The `vula repair` command will ensure that all peers have the correct routes
and wireguard peer configuration. It can be run with the `--dry-run` option to
print what would be corrected without actually modifying the system state. This
command should generally not find anything which needs to be repaired.

If you encounter problems while running vula and wish to stop the service, the
steps to do so are currently:

* `sudo systemctl stop vula.slice` to stop the software.
* `sudo ip link del vula` to delete the device and the routes.
* `sudo ip -4 rule delete 666 && sudo ip -6 rule delete 666` to remove the ip
  rules.

To prevent the daemons from launching on startup, you can run `systemctl
disable --now vula-organize` and/or `apt remove python3-vula`.

Please open an issue on codeberg if you encounter any problems!
