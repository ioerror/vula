# Vula: automatic local network encryption

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

# Security contact

We consider this project to currently be alpha pre-release, experimental, research-quality code. It is not yet suitable for widespread deployment. It has not yet been audited by an independent third party and should be treated with caution.

If you or someone you know finds a security issue, please [open an issue](https://codeberg.org/vula/vula/issues/new) or feel free to send an email to the `security at vula dot link`.

# Authors

The authors of vula are anonymous for now, while our paper is undergoing peer review.

# Acknowledgements

[`operation-vula.md`](https://codeberg.org/vula/vula/src/branch/main/www-vula/content/operation-vula.md) has some history about the name Vula.

Vula is not associated with or endorsed by the [WireGuard](https://www.wireguard.com/) project. WireGuard is a registered trademark of [Jason A.  Donenfeld](https://www.zx2c4.com/).

This project is funded through the [NGI Assure Fund](https://nlnet.nl/assure), a fund established by [NLnet](https://nlnet.nl) with financial support from the European Commission's [Next Generation Internet](https://ngi.eu) program. Learn more on the [NLnet project page](https://nlnet.nl/project/Vula#ack).



