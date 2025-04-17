Research: IPv6 considerations for vula

In the common setting of an IPv4 LAN using RFC1918 addresses, vula's automatic
encryption is applied to connections using the same IP addresses which clients
would be using without vula. This is desirable, because it can protect traffic
between applications which are using means other than vula's name system to
learn each other's addresses.

However, in IPv6 things are a bit different. We consider four categories of
IPv6 addresses which peers may use:

* Link-local addresses (fe80::/10)
* Addresses from RFC 4193's Unique Local Address (ULA) block (fc00::/7)
* Multicast addresses
* All other unicast addresses (including publicly-routable addresses)

The first category is link-local, the fe80::/10 addresses every interface has
bound. Addresses in this block are are specified to be unique only to a single
interface. The IPv6 address notation for them can optionally include %zone-id
appended to the address, where zone-id is a local identifier for the interface
it is related to. Binding these addresses to an interface with a scope other
than "link" is not possible in the Linux kernel, and we were unable to find a
way to use these IPs bound to a physical interface as a source address for
packets on a wireguard interface with no IPs bound to it the way that we we can
do with other types of addresses. We considered binding a doppelgänger of
the link-local addresses of each physical interface to a wireguard interface,
but rejected this approach because it would only be able to protect traffic
which obtained peer addresses along with the correct zone-id - meaning traffic
which is using our name system, which is traffic that can already get a
non-link-local address instead. We therefore do not protect application traffic
which uses physical interfaces' existing link-local addresses. It may be
possible to automatically encrypt fe80 traffic even with the correct zone-id
using nftables or other Linux technologies; future research in this area is
warranted.

We can, however, use these link-local addresses as our wireguard endpoints.

The second category, ULA, is the IPv6 analogue of IPv4's RFC1918 space, and we
can indeed protect it the same way that we do RFC1918 addresses. On networks
with presently-existing ULA addresses, adding vula can automatically encrypt
existing traffic using these addresses.

The third category, multicast, we will use for mDNS in the same manner as with
IPv4. We do not automatically encrypt multicast traffic.

The fourth category, public IPs, we will treat the same as non-RFC1918 IPv4
addresses: we do not accept peer descriptors using these addresses, and will
only route traffic to these addresses via vula if the current default route is
via a vula peer. This is analogous to how vula works with IPv4, in that it does
not protect traffic using public addresses, but it is more unfortunate because
in IPv6 it is far more likely that LANs are using public IPs.

LANs often have ULA addresses  alongisde public IPs, which vula can
automatically protect, but there are many settings where there no ULA addresses
being assigned. In a LAN without a router, there will be only self-assigned
link-local addresses.

Design: Vula's approach to IPv6 

In order to provide automatic encryption in the absence of ULA or RFC1918
addresses, we decided to make vula peers each generate their own ULA address
within a vula-specific network prefix.

We registered the fdff:ffff:ffdf::/48
block with the Ungleich IPv6 ULA registry for this purpose. These are the IPv6
addresses which vula names will now resolve to. The address is bound to
*localhost* rather than the vula interface, because having no address bound to
the vula interface is what enables the correct source IP to be determiend for
internet-bound traffic via a vula-enabled gateway. The vula-provided ULA
address is never used outside of the tunnel. Wireguard's encrypted traffic is
sent on the physical interface using link-local addresses.

Besides IPv6 connectivity in the absence of a router advertizing ULA prefixes,
this solution also provides vula-protected connectivity absent any router at
all. Also, previously, two IPv6-capable pinned peers who found themselves on a
network assigning only public IPv4 addresses would be unable to communicate
over vula: applications using vula to resolve names of pinned peers would
resolve to the last acceptable address they had, and these packes would be
routed to the wireguard interface where that pinned peer has a stale session
with an unroutable old IP and therefore cannot route traffic. Now, instead, the
hosts can resolve ULA IPs for each other and communicate using link-local
addresses for the wireguard packets.

Default route encryption in a LAN using ULA addresses and prefix translation
should work similarly to the way it works on IPv4 networks with RFC1918
addresses. In the more common IPv6 environment where clients are given public
IPs, a vula enabled router must add the subnet(s) that it advertizes to its
`subnets_allowed` list so that it will allow peers to route packets to it using
source addresses from that subnet.

To make automatic default route encruption possible, vula peers must now
announce all of their IP addresses that vula is enabled for including addresses
that are not in their `allowed_subnets` list. This will only work in the common
case that the announced route is actually a link-local address (in fe80::/10)
as this is what allows clients to identify the peer as their gateway. With the
default `subnets_allowed` settings peers will not recognize routers advertising
non-link-local addresses as the default route. We do not provide automatic
encryption for those routers in our default configuration.

In the course of implementing IPv6 support, a number of other issues were also
addressed, inclduing fixing support for multihomed hosts: now when vula is
enabled on multiple interfaces, different descriptors are sent on each with the
correct IP addresses for that interface.


