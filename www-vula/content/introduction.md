---
title: "Vula: Automatic local network encryption"
date: 2025-03-31T13:37:26-07:00
draft: false
---

Data transiting today\'s Internet is almost universally protected by TLS
encryption. This became true only after 2013 when whistleblowers and
press reports revealed that government intelligences agencies were
routinely spying on unencrypted Internet traffic. The Internet, as an
institution and as a community, responded by lowering technical and cost
barriers to encryption, while simultaneously enforcing new security
norms through default software policies.

Meanwhile, security practices on local-area networks (LANs) paint quite
a different picture, with the application of TLS to private networks
remaining the exception rather than the rule. Unencrypted LAN traffic is
consequently an attractive target for either external or internal threat
actors. Without encrypted communication between LAN hosts, the
compromise of a single host by whatever means can open the whole subnet
to passive or active surveillance.

The vula protocol, implemented by this project, brings self-configuring,
quantum-resistent encrypted tunneling to IPv4 LANs. A network with vula
running on each each host automatically configures encrypted
peer-to-peer tunneling between each host pair. Vula is completely
decentralized, avoiding a single point of failure. and uses existing IP
addresses inside and outside of tunnels, allowing seamless integration
into existing LAN environments that use either DHCP or static
addressing.

## vula definitions {#vula-definitions .list-paragraph}

The following definitions simplify understanding of the vula operations
described below.

-   **Descriptor lifetime (dl) --** Key-value pair specifying descriptor
    TTL. Reserved but not implemented.

-   **Ephemeral flag (e) --** Key-value pair in the descriptor. Reserved
    but not implemented.

-   **Ephemeral key (c)** **--** A temporary, hence mutable, CSIDH
    public key (base64-encoded) providing fresh key material for
    short-term exchanges and offering post-quantum security to the
    underlying encrypted tunnels.

-   **Peer public WireGuard key (pk) --** The current public WireGuard
    key (base64 encoded) used for active connection setups. The key is
    mutable and may change over time.

-   **Pinned/Verified vula peer --** A peer whose verification key has
    been verified out-of-band, making its descriptor permanently trusted
    and retained (except when manually removed).

-   **Pinning --** The state achieved when a vula peer's verification
    key is verified, marking the peer as permanently trusted for secure
    communication.

-   **Router flag (r) --** Indicates whether the vula peer functions as
    a network router.

-   **Signature (s) --** Ed25519 cryptographic signature over all the
    data in the vula descriptor.

-   **Unpinned/Unverified vula peer** **--** A peer whose verification
    key has not yet been confirmed out-of-band; its descriptor is
    temporary and subject to expiration or overwrite.

-   **Valid-from timestamp (vf) --** A timestamp in seconds since the
    Unix epoch indicating when the signature was generated.

-   **Verification --** To confirm that a vula peer's verification key
    is genuine, an out-of-band process is used, such as manual hash
    comparison, acoustical comparison, or QR code scanning. The command
    vula verify my-descriptor generates a QR code for the last of these
    cases.

-   **Verification key (vk) --** The immutable public key
    (base64-encoded) that uniquely identifies a vula peer. The key must
    be verified out-of-band to establish permanent trust.

-   **vula descriptor --** A compact key-value set containing a vula
    peer's connectivity information, cryptographic keys, and descriptive
    metadata.

-   **vula-enabled gateway** **--** A vula peer configured with the
    use_as_gateway property to act as a default gateway, offering
    WireGuard-encrypted connectivity and obfuscating external routing by
    presenting the gateway's IP as the destination in outer IP packets.

-   **vula peer --** A host computer running vula software. All
    components can be run at once with the command vula organize
    \--monolith.

## How vula works {#how-vula-works .list-paragraph}

Hosts running vula discover peers on their broadcast segment by using
zero-configuration [Multicast
DNS](https://datatracker.ietf.org/doc/html/rfc6762) and [DNS Service
Discovery](https://datatracker.ietf.org/doc/html/rfc6763) (mDNS-SD).
Handshakes with non-participating hosts are not attempted. Each vula
peer generates cryptographically bound metadata in the form of a vula
descriptor. To create the descriptor, the peer collects its preferred
endpoints (addrs), retrieves its current peer public WireGuard key (pk),
and generates an ephemeral key (c) for temporary exchanges. It then sets
its hostname (hostname) and port (port) for connectivity and includes
its immutable verification key (vk) as the permanent identifier.
Additional validity parameters are added, including the valid-from
timestamp (vf), the router flag (r), and other values not yet
implemented. Finally, a mandatory signature (s) is computed to bind the
ephemeral key (c) to the verification key (vk), ensuring integrity and
authenticity. The complete descriptor comprises {addrs, pk, c, hostname,
port, vk, vf, r, s}. The descriptor is shared with other vula peers via
mDNS-SD the vula publish and vula discover commands.

Upon receiving a descriptor, a vula peer validates the data structure
and checks the signature (s) to confirm that the ephemeral key (c) is
correctly bound to the verification key. Even with a cryptographically
valid descriptor, the associated peer remains *unpinned* (unverified)
its verification key is confirmed out-of-band. Vula confers automatic
security against passive adversaries on an unpinned peer, but once
verified, a *pinned* peer additionally posseses a sticky route that
other peers cannot claim, providing resistance to active adversaries.

## Post-quantum protection {#post-quantum-protection .list-paragraph}

An important feature of vula, and an improvement over TLS in its present
form, is the use of a transitionally secure post-quantum encryption
protocol. This does not mean resisting present-day active attacks using
a quantum computer (which are not known to exist), but rather to build
in resistance to an attacker who retains surveilled ciphertext in
anticipation of having access to a quantum computer in the future. vula
uses a hybrid encryption protocol, with CTIDH as implemented by
highctidh serving to achieve non-interactive post-quantum key agreement,
and Curve25519 providing proven contemporary security protections. Early
versions of vula used CSIDH as implemented in pure Python on the
Montgomery curve by the sibc library. This was implemented with p512
using the hvelu formula in a dummy-free style, and it used 10 as the
exponent. CSIDH is now replaced by CTIDH and is implemented with a
Python library highctidh backed by a formally verified C implementation.
CTIDH as used by vula has a 512-bit field size.

vula\'s post-quantum protection is not currently forward secret; that is
to say, an attacker who records ciphertext and later has a quantum
computer and somehow obtains a user\'s CTIDH secret key will be able to
decrypt the traffic. Rotating the CTIDH key is possible, but this does
not (yet) happen automatically.

CSIDH is a very new cryptographic primitive, having only been first
published in 2018 and currently being studied by many people in the
academic cryptography community. CTIDH is even newer. While we do not
know of any feasible attacks against it today, it would be inappropriate
to rely solely on such a new primitive. If CTIDH were to be broken, the
effect on vula would be a loss of post-quantum protection; however,
security against attackers without quantum computers is not dependent on
CTIDH in any way.

## Basic threat model {#basic-threat-model .list-paragraph}

Currently vula assumes a passive adversary model during the initial
setup and discovery time, and is resistant to active adversaries who
join the network after the fact only if the pin_new_peers preference is
enabled or if peers are manually pinned. This is similar to ssh when
discovered keys are cached for the first time. As with ssh, key
verification should be performed and it should happen through an
out-of-band secure channel. We provide a method to verify peers with QR
codes as well as through other command line tools.

Our goals for the vula project are very modest. We hope to help people
who are subject to various kinds of surveillance **--** especially in
the privacy of their homes, in public spaces, in internet exchange
networks, and other places **--** and to see this done in a distributed,
decentralized fashion, free of single points of failure, and taking into
account long-term surveillance adversaries. Some of these adversaries
will almost certainly have access to universal quantum computers able,
in time, to break the confidentiality of many currently deployed crypto
systems. We have attempted to design the vula system to withstand such
an adversary. However, we stress that this is experimental cryptography
that should improve protection of traffic, but that long term
protections are aspirational goals, not mathematical certainties. We
expect that the protocol can be improved and we welcome constructive
improvement suggestions.

## A note on the name {#a-note-on-the-name .list-paragraph}

The word "vula" means \"to open\" in several African languages.
[Operation Vula](https://vula.link/operation-vula/) was an effort by the
African National Congress toward the end of the South African apartheid
regime that created a home-grown cryptographic system for covert
communications. The operation provided an alternative to commercial
encryption systems that were suspected to be insecure by design.

# Cryptographic protocol visualization

We have [modeled the Vula protocol](./misc/vula.vp) using [Verifpal](https://verifpal.com/) ![Vula Verifpal model](./misc/vula.png)

# Security contact

We consider this project to currently be alpha pre-release, experimental, research-quality code. It is not yet suitable for widespread deployment. It has not yet been audited by an independent third party and should be treated with caution.

If you or someone you know finds a security issue, please [open an issue](https://codeberg.org/vula/vula/issues/new) or feel free to send an email to the `security at vula dot link`.

# Authors

The authors of vula are anonymous for now, while our paper is undergoing peer review.

# Acknowledgements

Vula is not associated with or endorsed by the [WireGuard](https://www.wireguard.com/) project. WireGuard is a registered trademark of [Jason A.  Donenfeld](https://www.zx2c4.com/).

This project is funded through the [NGI Assure Fund](https://nlnet.nl/assure), a fund established by [NLnet](https://nlnet.nl) with financial support from the European Commission's [Next Generation Internet](https://ngi.eu) program. Learn more on the [NLnet project page](https://nlnet.nl/project/Vula#ack).
