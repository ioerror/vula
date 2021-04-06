# vula: automatic local network encryption

With zero configuration, vula automatically encrypts IP communication between
hosts on a local area network in a forward-secret and transitionally
post-quantum manner to protect against passive eavesdropping.

With manual key verification and/or automatic key pinning and manual resolution
of IP or hostname conflicts, vula will additionally protect against
interception by active adversaries.

When the local gateway to the internet is a vula peer, internet-destined
traffic will also be encrypted.

Vula combines [WireGuard](https://www.wireguard.com/papers/wireguard.pdf) for
forward-secret point to point tunnels with
[mDNS](https://tools.ietf.org/html/rfc6762) and
[DNS-SD](https://tools.ietf.org/html/rfc6763) for local service announcements.
Vula further enhances the confidentiality of WireGuard tunnels by using
[CSIDH](https://csidh.isogeny.org/), a post-quantum non-interactive
key exchange primitive, to generate a peer-wise pre-shared
key for each WireGuard tunnel configuration.

Vula's advantages over some other solutions include:

* design is absent of single points of failure (SPOFs)
* avoids needing to attempt handshakes with non-participating hosts
* uses existing IP addresses inside and outside the tunnels, allowing
  seamless integration into existing LAN environments using DHCP and/or manual
  addressing
* does not require any configuration to disrupt passive surveillance
  adversaries
* simple verification with QR codes to disrupt active surveillance adversaries

# Status

Vula is functional today, although it has a number of known issues documented in the `TODO` file. It is ready for testing by people who are proficient with networking and the commandline. It is not yet ready for novice users to test without assistance.

If you encounter problems while running it, the steps to disable it are currently `sudo systemctl stop vula.slice` followed by `sudo ip link del vula`. Please open an issue on codeberg if you encounter any problems!

# Requirements

Currently, GNU/Linux is the only supported operating system. We plan to port
the software to other operating systems in the future.

The software has been developed and tested on Debian (bullseye), Mobian, and
Ubuntu (20.04 and 20.10). It is likely to work on other modern distributions.

# Installation

We do not yet have packages available for download, but you can build your own deb or wheel from a git checkout.

## option 1: build and install a Debian Package

* `sudo apt install --no-install-recommends wireguard wireguard-tools python3-yaml python3-click python3-nacl python3-schema python3-pip python3-pydbus python3-pyroute2 python3-pytest-runner python3-pytest python3-toml python3-py python3-packaging python3-pluggy python3-hkdf python3-ifaddr python3-cryptography python3-dbus python3-pygments python3-systemd python3-qrcode python3-all python-all fakeroot build-essential dh-python debhelper make gcc`
* `sudo pip3 install stdeb sibc` (note: unfortunately this step still requires installing stdeb, sibc, and its dependencies with pip as root - you can alternately build a deb of `sibc` but this procedure is not yet documented here. the stdeb version from Debian stable and Ubuntu 20.10 is insufficient, however.)
* `git clone --recurse-submodules https://codeberg.org/vula/vula`
* `cd vula`
* `make deb && sudo dpkg -i deb_dist/python3-vula_*_all.deb`

Installing the deb will automatically configure `nsswitch`, restart
`systemd-sysusers`, reload `dbus`, etc, and will tell `systemd` to enable and
start the `vula-organize` service.

## option 2: install with pip

If you don't mind installing many things using `sudo pip`, the software can be installed this way:

* `git clone --recurse-submodules https://codeberg.org/vula/vula`
* `cd vula`
* `python3 setup.py compile`
* `sudo pip install .`

After installing with pip, users will need to configure the system:
* `sudo vula configure nsswitch`
* `sudo systemctl daemon-reload`
* `sudo systemctl restart systemd-sysusers`
* `sudo systemctl reload dbus`
* `sudo systemctl enable --now vula-organize`

Vula can also be run without systemd, and/or in a single monolithic process
under systemd, but how to do so is not yet documented.

## Running vula

To see the current status:
* `vula`

To start vula (via dbus activation) if it is not started, or print the status
if it is:
* `vula start`

To see a list of subcommands:
* `vula --help`

To see a list of peers:
* `vula peer`

To see a list of peers, including disabled peers:
* `vula peer show --all`

To see descriptors and qrcodes for all enabled peers:
* `vula peer show -Dq`

To see the preferences:
* `vula prefs`

To see commands for editing preferences:
* `vula prefs --help`

More documentation is coming soon.

## Technical details and vision

The vula paper outlines the design decisions, the threat model, the vision for
the `vula` system as well as the `vula` protocol. Please send an email to
`paper at vula dot link` requesting a copy of our current draft while it is
under submission.

### IPv4 and IPv6 limitations

Currently, vula supports IPv4 for networks with [RFC 1918
addresses](https://tools.ietf.org/html/rfc1918) and will support IPv6 networks
in the future.  With a small amount of manual configuration, vula also supports
any other subnets desired if RFC 1918 address space isn't sufficient. 

### Secure local names

On GNU/Linux systems, vula connections are available if `vula configure
nsswitch` is run after installation of the vula package. This is performed
automatically during the installation process when using the Debian packages
produced by `make deb`. Absent an active attack or misconfiguration, our name
system will usually resolve hostnames of vula peers to the same IPs as mDNS
would, so it is possible to use vula without it. However, resolving names via
vula is required to achieve strong protection against active attackers.

### Post-quantum protection

Vula is designed as a transitionally secure post-quantum protocol. It does not
currently resist an active adversary with a quantum computer; it is designed to
resist an attacker that logs captured surveillance data in anticipation of
access to quantum computer at a later date. The vula protocol uses
[CSIDH](https://csidh.isogeny.org/) to achieve non-interactive post-quantum key
agreement in much the same way that Curve25519 is used for contemporary
security protections in the vula protocol. CSIDH is implemented in pure Python
on the Montgomery curve by the [sibc
library](https://github.com/JJChiDguez/sibc/). It is implemented with p512
using the hvelu formula in a dummy-free style, and it uses 10 as the exponent.

The post-quantum protection is not currently forward secret; that is, an
attacker who records ciphertext and later has a quantum computer *and* obtains a
user's CSIDH secret key will be able to decrypt the traffic. Rotating the CSIDH
key is possible, but this does not (yet) happen automatically.

### Default route encryption

The `vula organize` daemon will automatically secure traffic to the local
gateway when that gateway is also a vula peer.

This configuration provides a simple but effective method of protecting the
source and destination information of any traffic intended for the wider
internet. In an otherwise open wireless network scenario, the entire network
would normally be able to see the source and destination IP addresses of
connections to upstream resources. When this option is enabled, the outer IP
packets only reveal the IP addresses of the two peers on the network, while the
inner IP packets contain the destination or source of the upstream resource.
This does not prevent the router from seeing this traffic but it blinds all
other local network adversaries.

### Constraints

By design `vula` only attempts to add newly discovered peers in the same local
network segments where multicast DNS is currently used. Unpinned peers will be
automatically removed when they become no longer local (eg, due to no longer
having an IP bound in their subnet). Pinned peers will retain their routes, so
that traffic to them will fail closed in the event that a DHCP attacker has
moved us to a new subnet. This includes the default route, when the gateway is
a pinned peer, so explicit user action is necessary when connecting to a new
network after being in the presence of a pinned gateway peer (currently via
`vula peer set $peer_id use_as_gateway false`; in the future there will be a
`vula release-gateway` command).

## Threat Model Basics

Currently `vula` assumes a passive adversary model during the initial setup and
discovery time, and is resistant to active adversaries who join the network
after the fact only if the `pin_new_peers` preference is enabled or if peers
are manually pinned. This is similar to `ssh` when discovered keys are cached
for the first time. As with `ssh`, key verification should be performed and it
should happen through an out of band secure channel. We provide a method to
verify peers with QR codes as well as through other command line tools.

## Security and privacy goals

Our goals for the `vula` project are very modest. We hope to help people who
are subject to various kinds of surveillance - especially in the privacy of
their own home, in public spaces, in internet exchange network, and other
places - and we hope this is done in a distributed, decentralized fashion, one
that is free of single points of failure, and that it is done with long term
surveillance adversaries in mind. Some of these adversaries will almost
certainly have access to universal quantum computers that will, in time, be
able to break the confidentiality of many currently deployed crypto systems. We
have attempted to design the `vula` system to withstand such an adversary.
However, we must stress that this is experimental cryptography which should
improve protection of traffic, but long term protections are aspirational
goals, and not mathematical certainties. We expect that there are improvements
to be made to the protocol and we welcome constructive improvement suggestions.

# Security contact

We consider this project to currently be alpha pre-release, experimental,
research quality code.  It is not yet suitable for widespread deployment.  It
has not yet been audited by an independent third party and it should be treated
with caution.

If you or someone you know finds a security issue - please [open an
issue](https://codeberg.org/vula/vula/issues/new) or feel free to send an email
to `security at vula dot link`.

Our current bug bounty for security issues is humble. We will treat qualifying
reporters to a beverage after the COVID-19 crisis has ended; ojalá. Locations
limited to qualifying CCC events such as the yearly Congress.

# Acknowledgements

## A short history of the name vula

Vula is a word meaning "to open" in several African languages.

Operation Vula was a [clandestine effort by the
ANC](https://omalley.nelsonmandela.org/omalley/index.php/site/q/03lv03445/04lv03996/05lv04001.htm)
towards the end of the South African apartheid regime. One of the key tasks was
the [creation of a homegrown cryptographic
system](https://www.sahistory.org.za/sites/default/files/GarrettEdwards-RevolutionarySecrets-prepress.pdf).

Communications security systems such as these, designed by surveillance targets
themselves, are sometimes categorized as *indigenous cryptography* by
intelligence agencies.

The common wisdom at the time of Operation Vula was to rely on
commercially-available systems for any cryptographic need.  The implementations
of many of these systems were insecure by design, however. This intentional
weakness is consistent with the signals intelligence strategies of nations
which materially supported the apartheid regime in South Africa.

It was in this context in the late 1980s that [Tim
Jenkin](https://en.wikipedia.org/wiki/Tim_Jenkin) and Ronnie Press designed and
built a custom cryptographic solution for the ANC's revolutionary activities,
involving human couriers, tape recorders, payphones, portable computers,
information theoretically secure cryptography such as one-time pads, and
clandestine communications relays.

The original [vula connection](https://m.youtube.com/watch?v=29vrvKsKXPI) was
designed with an understanding that the crypto systems of the era were likely
untrustworthy, and that resistance to apartheid required strong cryptography
without backdoors. They considered the problems from first principles and were
successful by many measures.

We contacted Tim and asked for his permission to name this project in homage to
his work, and he encouraged us to do so and to use this as an opportunity to
tell people about [his
story](https://web.archive.org/web/20180722014538/http://www.anc.org.za/content/talking-vula/),
and about [stories of the
people](https://www.goodreads.com/book/show/114193.Operation_Vula)
who struggled against apartheid. We think Tim's work and the struggle he
supported is worth studying. We find it extremely inspiring and we hope that
others will too.

We also encourage everyone to take the time to watch the related film about
Tim's [escape](https://www.iol.co.za/weekend-argus/entertainment/escape-from-pretoria-tells-story-of-tim-jenkin-and-wooden-keys-49913457) [from
Pretoria prison](https://m.youtube.com/watch?v=0WyeAaYjlxE) where he was held
as a political prisoner by the racist apartheid regime. *[Escape from
Pretoria](https://en.wikipedia.org/wiki/Escape_from_Pretoria)* has recently been
retold as a major motion picture. We also encourage you to check out what Tim
is working on these days with his [Community Exchange
System](https://www.community-exchange.org/).

## WireGuard

Vula is not associated with or endorsed by the
[WireGuard](https://www.wireguard.com/) project. WireGuard is a registered
trademark of [Jason A.  Donenfeld](https://www.zx2c4.com/).
