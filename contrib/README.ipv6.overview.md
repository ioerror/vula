# Enhancing vula with IPv6

This document addresses enhancing vula with IPv6 support by breaking down the
various tasks into milestones:
a. Perform assessment of Python reference implementation
b. Research possibility of encrypting existing fe80 vs using vula-generated
  fc00 addresses
c. Write design document describing IPv6 plan
d. Implement plan for protecting either fe80 or fc00 addresses for LAN peer
  traffic
e. Implement plan for default route encryption
f. Add containerized integration tests of IPv6 functionality
g. Perform analysis and review of IPv6 implementation

Please refer to related documents in `vula/contrib/`:
- An early historical initial IPv6 assessment of the Python reference
  implementation: `vula/contrib/IPv6.initial.assessment.md`
- A concise research and design document for IPv6:
  `vula/contrib/`IPv6.research.design.md
- The testing and verification document for IPv6:
  `vula/contrib/IPv6.testing.md`

## Context for enhancing vula with IPv6

We defined our research context as a vula peer with some set of private IPv4
addresses and non-routable IPv6 addresses. Protection of a vula peer's IP
addresses is governed by the `vula organize prefs` values
`iface_prefix_allowed` and `subnets_allowed`. The `iface_prefix_allowed` is a
mask that is used in matches of interface names to be protected automatically.

In vula, we use policy based routing with `IPv4` without an IPv4 address bound
to the `vula` device to direct traffic to a vula peer. The current name
resolution process for vula IPv4 use a name resolution strategy specific to
glibc as implemented in [vula_libnss](https://codeberg.org/vula/vula_libnss).
The resolved address is the same as the peer's IPv4 endpoint.

The evaluation made by vula is to first look at the system interfaces and if
the interfaces match the following list of interfaces, the interfaces are
enumerated to check the IP addresses bound to the device:
```
iface_prefix_allowed:
- en
- eth
- wl
- thunderbolt
```

If an interface has one or more IPv4 addresses in any of the RFC1918 and
RFC3927 subnets listed then it is automatically considered as an address to be
protected by vula:
```
subnets_allowed:
- 10.0.0.0/8
- 192.168.0.0/16
- 172.16.0.0/12
- 169.254.0.0/16
```

For IPv6 enhancements to vula need to update functionality for vula such that
the `subnets_allowed` may include additional subnets for IPv6 IP addresses:
- Each interface with IPv6 enabled should have `fe80::/64`
- Each peer should have an IPv6 Unique Local Address such as an example in our
  own Unique Local Address (ULA) block of `fd::`
- Optionally if a LAN is not airgapped, a user may experimentally set public
  IPv6 addresses at their own risk.

The primary research questions that we identified are as follows:
0. Is it possible to use `fe80::/64` addresses as peer endpoints? 
1. It is possible for vula to operate without DHCPv4 or DHCPv6 given the
  requirement of automatic `fe80::/64` addresses in IPv6 enabled networks?
2. It is possible we protect `fe80::/64` addresses?
3. Is it possible to register a ULA prefix `fd::/` for use in vula?
4. Is it possible to protect the `fd::/` addresses with vula as we would any
  other IP in `subnets_allowed`?
5. Will `vula_libnss` continue to be a viable way to resolve vula peer names
  to an IPv4 and/or an IPv6 address for the peer?
6. Is it possible to protect internet destined traffic on non-airgapped
  networks for IPv6 with only non-public addresses as we do with IPv4?
7. Is it possible to protect internet destined traffic on non-airgapped
  networks for IPv6 with public addresses as we do with IPv4?
8. Is it possible for IPv4 only vula hosts to bidirectionally communicate with
  IPv4/IPv6 dual-stack vula peers?
9. Is it possible to enhance vula's protection to use a multilayered security
  enforcement approach to ensure IP packets destined for vula peers are not sent
  unencrypted to the local-area network?
10. Is it possible to construct meaningful integration tests in a container
  framework or are virtual machines required?
11. Given answers to items zero through ten, what is the minimal viable IPv6
  enhancement to vula to protect IPv6 enabled vula hosts in an airgapped or NAT
  context?
12. What discrete problems need to be solved generally that would benefit other
  projects?

## Milestone A: Perform assessment of Python reference implementation

We began our work to answer our research questions with an initial assessment
of the vula codebase to see if various functions were suitable to use with IPv4
and IPv6 addresses. This assessment scope with results are documented in
`contrib/IPv6.initial.assessment.md`. This initial assessment contains findings
related to handling of IPv6 addresses in an abstract sense. The assessment did
not consider possible changes to the vula descriptor format, or differences
with IPv6 such as the often mandatory link-scope identifier included in various
networking operations. The initial assessment concluded that that the vula
codebase required refactoring regardless of which address blocks would be added
to `allowed_subnets`. We also found that further analysis would require better
understanding items zero through six to better understand the specific
differences with IPv4.

## Milestone B: Research encrypting existing and synthetic addresses

Our research methodology for Milestone B consisted of iterative development to
first resolve all incompatibilities with IPv6 in the vula codebase as discussed
in Milestone A, and with registration of a block of IPv6 ULA addresses for
vula's use.

### Operation using autonomously assigned IPv6 addresses

In research question zero we ask: "Is it possible to use `fe80::/64` addresses
as peer endpoints?" and in research question one we ask: "It is possible for
vula to operate without DHCPv4 or DHCPv6 given the requirement of automatic
`fe80::/64` addresses in IPv6 enabled networks?"

The underlying tunneling device used by vula is a WireGuard device that allows
setting a peer endpoint as an `fe80::` address including with an optional link
scope identifier. We previously configured the local `vula` device to set a
firewall mark of `0x22b` for all encrypted packets originating from the local
vula device. This firewall mark is metadata local to the vula host system and
may be used for policy based routing, in addition to other IP packet flow and
state management strategies.

Our experimental findings for research question include:
- Setting the vula peer's endpoint to be an `fe80::/128` with a link scope
  identifier is a viable strategy for bidirectional communication between vula
  peers
- Automatic addressing of `fe80::/64` removes the need for manual address
  configuration in an otherwise empty network
- The use of link-local addresses for peer endpoints allows for regular
  rotation of addresses as seen by a third party adversary monitoring traffic
- The continued use of a firewall mark may allow for routing of endpoint addresses
  over the vula device such that the primary IP traffic visible on the local
  network segment is peer to peer WireGuard encrypted IP packets
- To ensure communication with IPv4 only vula hosts, IPv6 enabled hosts are
  required to have at least one IPv4 address bound to a vula protected
  interface that is in the default `subnets_allowed`

We conclude through experimentation that the answer to research question zero
and one is yes, and so IPv6 enabled vula peers listen on their respective
link-local `fe80::/128` addresses as their primary endpoint. All IPv6 enabled
vula peers may operate completely independently of any local network
infrastructure such as DHCP servers or manual addressing while also continuing
to support vula hosts which are configured in either manner.

#### Protecting `fe80::/64` with vula

In research question two we ask: "It is possible we protect `fe80::/64`
addresses?" There are several notions of protection that we considered during
the course of our research including transparently encrypting traffic destined
for or originating from a vula peer's `fe80::/128` address. There are several
use cases where a user might accidentally resolve a peer's name that results in
an `fe80::/128` address with or without a scope identifier.

In vula, we use policy based routing with `IPv4` without an IPv4 address bound
to the `vula` device to direct traffic to a vula peer. Policy based routing for
IPv6 generally works similarly to IPv4 with the exception of `fe80::/10`
addresses which are marked as `link-local`.

We surveyed the possible strategies for directing IP traffic where the two
tuple of source and destination IPv4 or IPv6 are for the vula host and its
respective vula peer. We confirmed that the Linux traffic control subsystem was
able to perform relevant fine grained redirection of all peer packets
regardless of any special address or link-scope identifier considerations. The
use of eBPF with XDP or the use of eBPF with tc for packet processing are two
additional areas for ensuring policy compliance of packets destined to or
originating from vula peers.

### Generated ULA addresses

In research question three we ask: "Is it possible to register a ULA prefix
`fd::/` for use in vula?"

While registration is not strictly necessary as the `fc00::/7` block as defined
in RFC6724 is free for ULA use. The `fc00::/7` block is split into `fc00::/8`
and `fd00::/8` with the latter carved out for unofficial registration to signal
intent to use for specific use. We registered the prefix `fdff:ffff:ffdf::/48`
in the [https://ula.ungleich.ch/](Ungleich ULA registry) to signal our
intention to use this address space for vula peers.  This provides vula with
`1208925819614629174706176` IPv6 addresses.

We conclude that it is possible to register a prefix, though it is not
required, and so we have registered `fdff:ffff:ffdf::/48` for use as the
default IPv6 peer address. We call a vula host's `fd::/128` their synthetic
IPv6 address.

### ULA address use and their lifetime

To use an address in `fd00::/8`, we decided to assign them randomly with no
guarantee of their lifetime. A peer may or may not keep their `fd::` addresses
and updates to this address are propagated as any other property of a vula peer
through mutual vula descriptor exchange. 

This address, while nominally ephemeral, could serve as the primary IPv6
address when vula peers look up their respective peer's IPv6 address by their
vula protected name.


### ULA addresses

In research question four we ask: "Is it possible to protect the `fd::/`
addresses with vula as we would any other IP in `subnets_allowed`?" The
protection notion is similar to the `fe80::/64` traffic. Is it possible for
vula to automatically encrypted traffic originating from a vula peer's `fd::/8`
and to another vula peer's `fd::/8` when they are on the same network segment?

We create a virtual interface that is bound on a vula host with a single
`fd::/8` address. Including this address in generated vula descriptors was
possible after the IPv6 enhancements to ensure all required functions were
compatible with IPv4 and IPv6. We additionally modified the `subnets_allowed`
to include `fd::/8`:
```
subnets_allowed:
- 10.0.0.0/8
- 192.168.0.0/16
- 172.16.0.0/12
- 169.254.0.0/16
- fd::/8
```

There are a number of benefits to having a stable, unique IPv6 address on a
peer by peer basis including the ability to move between networks while
maintaining open TCP/IP connections regardless of the IP addressing of the
local network's IP address assignment policy.

We conclude yes, it is indeed possible to protect `fd::/8` addresses. It is
even desirable to resolve the remote peer's primary IPv6 address to a peer
controlled IPv6 address rather than relying solely on what happens to be on any
given network interface in any given moment.

In research question five we ask: "Will `vula_libnss` continue to be a viable
way to resolve vula peer names to an IPv4 and/or an IPv6 address for the peer?"

Through review of the source code for the glibc `vula_libnss` module, we
conclude that `vula_libnss` continues to be a viable method of name resolution
for both IPv4 and IPv6 addresses of peer names.

# Milestone C: Write design document describing IPv6 plan

The canonical design document for IPv6 is located in
`contrib/IPv6.research.design.md`.

A summary of the aforementioned design document for IPv6 support in the Python
reference implementation of vula follows from the answers to our research
questions:

- Use existing `fe80::/64` endpoints configured automatically by the Linux
  kernel for peers with or without a link scope identifier for their WireGuard
  endpoint on the same network segment
- Create, manage, and assign an address in a subnet under `fc00::/7` as the
  primary IPv6 address for vula name resolution of IPv6 addresses
- Protection of the IPv6 default route is possible using similar heuristics as
  default route protection in IPv4

# Milestone D: Implement plan for protecting either fe80 or fc00 addresses

The `ipv6` branch in the vula repository represents the implementation for the
research results and the instantiation of the design document describing our
IPv6 plan. It uses a single `fe80::/128` with an interface scope for its own
WireGuard peer endpoint configuration, and it uses an address in the vula IPv6
ULA block  `fdff:ffff:ffdf::/48` of IPv6 addresses. In addition to many other
IPv6 related enhancements to realize IPv6 support in vula.

The initial research results using the traffic control subsystem allow us to
redirect, route, and otherwise prevent packets addressed two and from
`fe80::/128` addresses from leaking when they belong to a vula peer. This
experimental protection still allows for other non-vula `fe80::` traffic to
pass without issue but we have not yet adopted it by default. This means that
while we are able to protect `fe80::` traffic selectively, we currently have
not included an implementation pending further real world deployment testing.

# Milestone E: Implement plan for default route encryption

In research question six we ask: "Is it possible to protect internet destined
traffic on non-airgapped networks for IPv6 with only non-public addresses as we
do with IPv4?"

IPv4 default route encryption protected by a vula peer that is already the vula
peer's gateway remains unchanged and continues to work. This functionality
depends on the vula peer performing NAT for IP4 or otherwise routing the
traffic upstream. The `ipv6` branch in the vula repository implement default
route encryption for IPv6 where the vula gateway peer must perform NAT66 or
NPTv6 for traffic originating from the vula peer's already existing ULA
addresses as assigned on the local network segment. As an example, if a vula
peer or another router provides a site specific ULA to vula peers, the vula
peers will use the ULA addresses in a protected fashion automatically. We
conclude that the answer to the sixth research question is yes if the
local-area network provides a ULA prefix for the LAN that is shared between all
vula peers and if the vula peer acting as a gateway performs prefix translation
to one or more public addresses.

In research question seven we ask: "Is it possible to protect internet destined
traffic on non-airgapped networks for IPv6 with public addresses as we do with
IPv4?"

Experimentally and not enabled by default, vula peers may optionally be
configured with public addresses. The configuration is currently manual and
must be symmetric amongst all peers. Note however that the vula project does
not currently encourage the use of public addresses as their use in the vula
context lacks a written security analysis. Nonetheless we conclude that yes,
research question seven is possible.

In research question eight we ask: "Is it possible for IPv4 only vula hosts to
bidirectionally communicate with IPv4/IPv6 dual-stack vula peers?"

We conclude that it is possible as long as the IPv6 host has an overlapping
subnet with the IPv4 only vula host.

In research question nine we ask: "Is it possible to enhance vula's protection
to use a multilayered security enforcement approach to ensure IP packets
destined for vula peers are not sent unencrypted to the local-area network?"

As previously mentioned in `Protecting `fe80::/64` with vula`, the use of the
Linux traffic control subsystem is a lower layer subsystem is able to augment
technical measures at other layers to enforce a consistent vula peer policy
that ensures peer packets do not leak in unexpected ways.

# Milestone F: Add containerized integration tests of IPv6 functionality

In research question ten we ask: "Is it possible to construct meaningful
integration tests in a container framework or are virtual machines required?"

The `ipv6` branch in the vula repository includes parameterized container based
integration tests using podman. The containerized integration tests include the
ability to test vula networks of arbitrary sizes that are constrained only by
the resources of the host system. We conclude that it is not only possible, it
is extremely practical and the size of the simulated vula network scales
proportionate to the resources of the container host system. Virtual machines
may be useful for certain future integration testing and podman containers are
suitable for the current integration tests.

# Milestone G: Perform analysis and review of IPv6 implementation

In research question eleven we ask: "Given answers to items zero through ten,
what is the minimal viable IPv6 enhancement to vula to protect IPv6 enabled
vula hosts in an airgapped or NAT context?"

An initial review and subsequent reviews were performed. Changes made in
response to the review have been included in the main branch and in the `ipv6`
branch. A final review has been be performed and there were no significant
findings following the previous reviews. We conclude that the answer to
research question eleven is the design and implementation present in the `ipv6`
branch, and that it should be merged.

In research question twelve we ask: "What discrete problems need to be solved
generally that would benefit other projects?"

During the course of developing and auditing the `ipv6` branch, we began to
write a policy enforcement module that ensures that IP traffic destined for
vula peers does not leak or traverse an incorrect network device or segment.
This module is a prototype has a working name of `guardrail` and it provides a
modular, layered security enforcement boundary. Given a policy object
consisting of peer IP addresses, endpoints, and network interface names, it
enforces a uniform policy using several complementary subsystems such as the
Linux traffic control subsystem, eBPF capable networking subsystems, netfilter,
and related policy based routing. An initial release of `guardrail` should be
made once a final peer traffic enforcement strategy has been tested in various
environments with documented configurations for a variety of common user
stories. We conclude that at the very least for research question twelve that
this policy enforcement module is worth solving generally to the benefit of
other projects.

# Instructions for testing the `ipv6` branch

Testing the `ipv6` branch is possible using podman and as well by building
packages and installing vula on a normal Ubuntu 24.10 system. Other systems are
possible but some other operating systems lack certain dependencies.

See `contrib/IPv6.testing.md` for detailed information regarding verification
and testing of the `ipv6` branch.
