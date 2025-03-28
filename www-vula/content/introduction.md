---
title: "Vula: automatic local network encryption"
date: 2025-03-28T13:37:26-07:00
draft: false
---

Requiring zero configuration, vula automatically encrypts IP communications between hosts on a local area network. The encryption is forward-secret, transitionally post-quantum, and protective against passive eavesdropping.

Vula will additionally protect against interception by active adversaries with the addition of manual key verification and/or automatic key pinning, along with manual resolution of IP or hostname conflicts.

If the local gateway to the internet is a vula peer, internet-destined traffic will also be encrypted on the LAN.

#How does it work?

Automatically.

Vula combines [WireGuard](https://www.wireguard.com/papers/wireguard.pdf) for forward-secret point-to-point tunnels with [mDNS](https://tools.ietf.org/html/rfc6762) and [DNS-SD](https://tools.ietf.org/html/rfc6763) for local service announcements, and enhances the confidentiality of WireGuard tunnels by using [CTIDH](https://ctidh.isogeny.org/software.html) implemented by [highctidh](https://codeberg.org/vula/highctidh), a post-quantum non-interactive key exchange primitive, to generate a peer-wise pre-shared key for each tunnel configuration.

Vula's advantages over other solutions include:

* The Vula design avoids single points of failure (SPOFs).
* Vula uses existing IP addresses inside and outside of tunnels, allowing seamless integration into existing LAN environments using DHCP and/or manual addressing.
* Vula avoids handshake attempts with non-participating hosts.
* Vula does not require additional configuration to disrupt passive surveillance adversaries.
* Vula provides simple verification with QR codes to disrupt active surveillance adversaries.

See [`Comparison of LAN tunneling tools`](https://codeberg.org/vula/vula/src/branch/main/www-vula/content/comparison.md) for a detailed comparison of Vula to related projects.

# Current status

[![status-badge](https://ci.codeberg.org/api/badges/vula/vula/status.svg)](https://ci.codeberg.org/vula/vula)

Vula is functional today, although with issues documented in [`STATUS.md`](https://codeberg.org/vula/vula/src/branch/main/STATUS.md). It is ready for daily use by people who are proficient with Linux networking and the command line.

See [`INSTALL.md`](https://codeberg.org/vula/vula/src/branch/main/INSTALL.md) for installation and usage instructions.

See [`hacking.md`](https://codeberg.org/vula/vula/src/branch/main/www-vula/content/hacking.md) for tips on opening the hood and dependency information about internal and external python modules.

# Basic vula threat model

Currently `vula` assumes a passive adversary model during the initial setup and discovery time, and is resistant to active adversaries who join the network after the fact only if the `pin_new_peers` preference is enabled or if peers are manually pinned. This is similar to `ssh` when discovered keys are cached for the first time. As with `ssh`, key verification should be performed and it should happen through an out-of-band secure channel. We provide a method to verify peers with QR codes as well as through other command line tools.

## Security and privacy goals

Our goals for the `vula` project are very modest. We hope to help people who are subject to various kinds of surveillance - especially in the privacy of their homes, in public spaces, in internet exchange networks, and other places - and to see this done in a distributed, decentralized fashion, free of single points of failure, and taking into account long-term surveillance adversaries. Some of these adversaries will almost certainly have access to universal quantum computers able, in time, to break the confidentiality of many currently deployed crypto systems. We have attempted to design the `vula` system to withstand such an adversary. However, we stress that this is experimental cryptography that should improve protection of traffic, but that long term protections are aspirational goals, not mathematical certainties. We expect that the protocol can be improved and we welcome constructive improvement suggestions.

# Post-quantum protection

Vula is designed as a transitionally secure post-quantum protocol, meaning that it does not currently resist active attacks using a quantum computer, but is designed rather to resist an attacker that retains surveilled ciphertext in anticipation of having access to a quantum computer in the future. Vula uses a hybrid encryption protocol, with [CTIDH](https://ctidh.isogeny.org/software.html) as implemented by [highctidh](https://codeberg.org/vula/highctidh) serving to achieve non-interactive post-quantum key agreement, and Curve25519 providing contemporary security protections. Early versions of vula used CSIDH as implemented in pure Python on the Montgomery curve by the [sibc library](https://github.com/JJChiDguez/sibc/). It was implemented with p512 using the hvelu formula in a dummy-free style, and it uses 10 as the exponent. CSIDH is now replaced by CTIDH and is implemented with a Python library [highctidh](https://codeberg.org/vula/highctidh/) backed by a formally verified C implementation. CTIDH as used by vula has a 512-bit field size.

Vula's post-quantum protection is not currently forward secret; that is to say, an attacker who records ciphertext and later has a quantum computer *and* somehow obtains a user's CTIDH secret key will be able to decrypt the traffic. Rotating the CTIDH key is possible, but this does not (yet) happen automatically.

CSIDH is a very new cryptographic primitive, having only been first published in 2018 and currently being studied by many people in the academic cryptography community. CTIDH is even newer. While we do not know of any feasible attacks against it today, it would be inappropriate to rely solely on such a new primitive. In the event that CTIDH were to be broken, the effect on vula would be a loss of post-quantum protection; security against attackers without quantum computers is not dependent on CTIDH in any way.

# Other considerations when using vula

## IPv4 and IPv6 limitations

Currently, vula's fully automatic configuration only applies to IPv4 networks using [RFC 1918 addresses](https://tools.ietf.org/html/rfc1918). With a small amount of manual configuration, vula could be used with non-RFC1918 IPv4 subnets.

We will support IPv6 networks in the future. There are several scenarios to consider for IPv6 support:

* link-local (`fe80`) addresses only
* On Ubuntu and other distros today, by default these are advertised by avahi if no other addresses are configured, but they are not actually resolved unless the querying user has enabled them by replacing `mdns4_minimal` with `mdns_minimal` in `/etc/nssswitch.conf`.
* Public IPs configured, and a default route
* ULA addresses configured, without a default route
* ULA addresses configured, with a default route (NAT)

##  Secure local names

On GNU/Linux systems, vula connections are available if `vula configure nsswitch` is run after installation of the vula package. If you use the Debian packages produced by `make deb`, this happens automatically during installation. Absent an active attack or misconfiguration, our name system will usually resolve hostnames of vula peers to the same IPs as mDNS would, so it is possible to use vula without it. However, resolving names via vula is required to achieve strong protection against active attackers.

## Default route encryption

The `vula organize` daemon will automatically secure traffic to the local gateway when that gateway is also a vula peer.

This configuration provides a simple but effective method of protecting the source and destination information of any traffic intended for the wider internet. In an otherwise open wireless network scenario, the entire network would normally be able to see the source and destination IP addresses of connections to upstream resources. When this option is enabled, the outer IP packets only reveal the IP addresses of the two peers on the network, while the inner IP packets contain the destination or source of the upstream resource. This does not prevent the router from seeing this traffic but it blinds all other local network adversaries.

## Constraints

By design, `vula` only attempts to add newly discovered peers in the same local network segments where multicast DNS is currently used. Unpinned peers will be automatically removed when they become no longer local, for example, due to no longer having an IP bound in their subnet. Pinned peers will retain their routes, so that traffic to them will fail closed in the event that a DHCP attacker has moved us to a new subnet. This includes the default route when the gateway is a pinned peer, so the explicit user action of running `vula release-gateway` is necessary when connecting to a new network after being in the presence of a pinned gateway peer.

# Cryptographic protocol visualization

We have [modeled the Vula protocol](./misc/vula.vp) using [Verifpal](https://verifpal.com/) ![Vula Verifpal model](./misc/vula.png)

# Security contact

We consider this project to currently be alpha pre-release, experimental, research-quality code. It is not yet suitable for widespread deployment. It has not yet been audited by an independent third party and should be treated with caution.

If you or someone you know finds a security issue, please [open an issue](https://codeberg.org/vula/vula/issues/new) or feel free to send an email to the `security at vula dot link`.

# Authors

The authors of vula are anonymous for now, while our paper is undergoing peer review.

# Acknowledgements

[`operation-vula.md`](https://codeberg.org/vula/vula/src/branch/main/www-vula/content/operation-vula.md) has some history about the name Vula.

Vula is not associated with or endorsed by the [WireGuard](https://www.wireguard.com/) project. WireGuard is a registered trademark of [Jason A.  Donenfeld](https://www.zx2c4.com/).

This project is funded through the [NGI Assure Fund](https://nlnet.nl/assure), a fund established by [NLnet](https://nlnet.nl) with financial support from the European Commission's [Next Generation Internet](https://ngi.eu) program. Learn more on the [NLnet project page](https://nlnet.nl/project/Vula#ack).






