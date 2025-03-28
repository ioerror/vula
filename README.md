# vula: automatic local network encryption

With zero configuration, vula automatically encrypts IP communications between
hosts on a local area network in a forward-secret and transitionally
post-quantum manner to protect against passive eavesdropping.

With manual key verification and/or automatic key pinning and manual resolution
of IP or hostname conflicts, vula will additionally protect against
interception by active adversaries.

When the local gateway to the internet is also a vula peer, internet-destined
traffic will also be encrypted on the LAN.

### How does it work?

Automatically.

Vula combines [WireGuard](https://www.wireguard.com/papers/wireguard.pdf) for
forward-secret point-to-point tunnels with
[mDNS](https://tools.ietf.org/html/rfc6762) and
[DNS-SD](https://tools.ietf.org/html/rfc6763) for local service announcements,
and enhances the confidentiality of WireGuard tunnels by using
[CTIDH](https://ctidh.isogeny.org/software.html) implemented by
[highctidh](https://codeberg.org/vula/highctidh), a post-quantum
non-interactive key exchange primitive, to generate a peer-wise pre-shared key
for each tunnel configuration.

Vula's advantages over other solutions include:

* The Vula design avoids single points of failure (SPOFs).
* Vula uses existing IP addresses inside and outside of tunnels, allowing
  seamless integration into existing LAN environments using DHCP and/or manual
  addressing.
* Vula avoids handshake attempts with non-participating hosts.
* Vula does not require additional configuration to disrupt passive surveillance
  adversaries.
* Vula provides simple verification with QR codes to disrupt active surveillance adversaries.

See [`NOTES.md`](https://codeberg.org/vula/vula/src/branch/main/NOTES.md) for
discussion of the threat model and other technical details, and
[`COMPARISON.md`](https://codeberg.org/vula/vula/src/branch/main/COMPARISON.md)
for a comparison of Vula to related projects.

### Current status

[![status-badge](https://ci.codeberg.org/api/badges/vula/vula/status.svg)](https://ci.codeberg.org/vula/vula)

Vula is functional today, although with issues documented in
[`STATUS.md`](https://codeberg.org/vula/vula/src/branch/main/STATUS.md). It is
ready for daily use by people who are proficient with Linux networking and the
command line, but we do not yet recommend it for people who are not.

See [`INSTALL.md`](https://codeberg.org/vula/vula/src/branch/main/INSTALL.md) for
installation and usage instructions.

See [`HACKING.md`](https://codeberg.org/vula/vula/src/branch/main/HACKING.md) for
some tips on opening the hood.

See [`DEPENDENCY.md`](DEPENDENCY.md) for diagrams illustrating the different
dependency relationships between internal and external python modules.

### Security contact

We consider this project to currently be alpha pre-release, experimental,
research quality code. It is not yet suitable for widespread deployment. It
has not yet been audited by an independent third party and should be treated
with caution.

If you or someone you know finds a security issue, please [open an
issue](https://codeberg.org/vula/vula/issues/new) or feel free to send an email
to the `security at vula dot link`.

### Authors

The authors of vula are anonymous for now, while our paper is undergoing peer
review.

### Acknowledgements

[`OPERATION_VULA.md`](https://codeberg.org/vula/vula/src/branch/main/OPERATION_VULA.md)
has some history about the name Vula.

Vula is not associated with or endorsed by the
[WireGuard](https://www.wireguard.com/) project. WireGuard is a registered
trademark of [Jason A.  Donenfeld](https://www.zx2c4.com/).

This project is funded through the [NGI Assure Fund](https://nlnet.nl/assure),
a fund established by [NLnet](https://nlnet.nl) with financial support from the
European Commission's [Next Generation Internet](https://ngi.eu) program. Learn
more on the [NLnet project page](https://nlnet.nl/project/Vula#ack).
