Vula peers may optionally act as a gateway that announces or assigns IPv4 or
IPv6 prefixes.  One option for publishing an IPv6 prefix is to use
`systemd-networkd` for prefix announcement. The `systemd-networkd` package on
Debian GNU/Linux or Ubuntu may be configured using the example configuration
files in this directory by placing them in `/etc/systemd/network/` for
publishing a vula compatible ULA to the local-area network.
