The upcoming vula paper outlines the design decisions, threat model, and vision
for the `vula` software and protocol. Please send an email to `paper at vula
dot link` requesting a copy of our current draft while it is under peer review.


## Cryptographic protocol visualization

We have [modeled the Vula protocol](./misc/vula.vp) using
[Verifpal](https://verifpal.com/) ![Vula Verifpal model](./misc/vula.png)

## IPv4 and IPv6 limitations

Currently, vula's fully automatic configuration is only applied to IPv4
networks using [RFC 1918 addresses](https://tools.ietf.org/html/rfc1918).
With a small amount of manual configuration, vula can be used with non-RFC1918
IPv4 subnets.

We will support IPv6 networks in the future. There are several scenarios to
consider for IPv6 support:

* link-local (`fe80`) addresses only
  * On Ubuntu and other distros today, by default these are advertised by avahi if no other addresses 
    are configured, but they are not actually resolved unless the querying user has enabled them by 
    replacing `mdns4_minimal` with `mdns_minimal` in `/etc/nssswitch.conf`.
* Public IPs configured, and a default route
* ULA addresses configured, without a default route
* ULA addresses configured, with a default route (NAT)


##  Secure local names

On GNU/Linux systems, vula connections are available if `vula configure
nsswitch` is run after installation of the vula package. This is performed
automatically during the installation process when using the Debian packages
produced by `make deb`. Absent an active attack or misconfiguration, our name
system will usually resolve hostnames of vula peers to the same IPs as mDNS
would, so it is possible to use vula without it. However, resolving names via
vula is required to achieve strong protection against active attackers.

## Post-quantum protection

Vula is designed as a transitionally secure post-quantum protocol, meaning that
it does not currently resist active attacks using a quantum computer but rather
is designed to resist an attacker that retains surveiled ciphertext in
anticipation of having access to quantum computer at a later date. The vula
protocol uses [CSIDH](https://csidh.isogeny.org/) to achieve non-interactive
post-quantum key agreement in much the same way that Curve25519 is used for
contemporary security protections in the vula protocol. CSIDH is implemented in
pure Python on the Montgomery curve by the [sibc
library](https://github.com/JJChiDguez/sibc/). It is implemented with p512
using the hvelu formula in a dummy-free style, and it uses 10 as the exponent.

Vula's post-quantum protection is not currently forward secret; that is to say,
an attacker who records ciphertext and later has a quantum computer *and*
somehow obtains a user's CSIDH secret key will be able to decrypt the traffic.
Rotating the CSIDH key is possible, but this does not (yet) happen
automatically.

CSIDH is a very new cryptographic primitive, having only been first published
in 2018 and currently being studied by many people in the academic cryptography
community. While we do not know of any feasible attacks against it today, it
would be inappropriate to rely solely on such a new primitive. In the event
that CSIDH were to be broken, the effect on vula would be a loss of
post-quantum protection; security against attackers without quantum computers
is not dependent on CSIDH in any way.

## Default route encryption

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

## Constraints

By design `vula` only attempts to add newly discovered peers in the same local
network segments where multicast DNS is currently used. Unpinned peers will be
automatically removed when they become no longer local (eg, due to no longer
having an IP bound in their subnet). Pinned peers will retain their routes, so
that traffic to them will fail closed in the event that a DHCP attacker has
moved us to a new subnet. This includes the default route, when the gateway is
a pinned peer, so explicit the explicit user action of running `vula
release-gateway` is necessary when connecting to a new network after being in
the presence of a pinned gateway peer.

## Threat Model Basics

Currently `vula` assumes a passive adversary model during the initial setup and
discovery time, and is resistant to active adversaries who join the network
after the fact only if the `pin_new_peers` preference is enabled or if peers
are manually pinned. This is similar to `ssh` when discovered keys are cached
for the first time. As with `ssh`, key verification should be performed and it
should happen through an out of band secure channel. We provide a method to
verify peers with QR codes as well as through other command line tools.

### Security and privacy goals

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


