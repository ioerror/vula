There are a wide variety of tools which can be used to create end-to-end
encrypted tunnels between hosts, or which share other superficial similarities
with Vula. To our knowledge, however, none of them achieve Vula's design goal
of providing fully-automatic end-to-end encryption of local area network
traffic.

The following is a list of unique properties which Vula provides:
* No infrastructure required
* Fully automatic: LAN traffic between hosts with Vula installed is protected without any configuration whatsoever
* Works on offline networks (eg, with RFC 3927 link-local addressing on ethernet, ad-hoc wifi, thunderbolt, etc)
* Protects traffic using existing IP addresses (whether DHCP-assigned, link-local, or manually configured), so applications do not need to be reconfigured
* Transitional post-quantum protection

Projects such as [Tailscale](https://tailscale.com/),
[Headscale](https://github.com/juanfont/headscale), and
[innernet](https://github.com/tonarino/innernet) are similar to Vula in that
they can be used to encrypt traffic between hosts on a LAN using WireGuard
tunnels, but they differ in some important respects:

* They only create tunnels between hosts that are logged in to the same account on a centralized coordination server.
    * Tailscale outsources the operation of this component to Amazon, a surveillance actor
    * Headscale and innernet provide free software implementations which can be self-hosted, but remain a single point of failure
* They use a different IP range inside and outside of the tunnels, so LAN-based applications need to be reconfigured to benefit from it.
* They do not provide any post-quantum protection

With the exception of TCPcrypt and IPsec OE, the other projects listed here are
all designed to protect traffic between hosts which are configured to be part
of a single organization, whereas Vula provides automatic encryption of traffic
between *all* locally-reachable hosts that are running the software.

TCPcrypt is an outlier, in that it does provide opportunistic encryption
between hosts without any configuration; however, it only protects TCP traffic,
does not provide secure names, and its key verification system requires
application-specific support. These and other deployment impediments have
prevented its adoption.

IPsec OE also is designed to provide opportunistic encryption, but has [numerous](https://nohats.ca/wordpress/blog/2013/09/12/history-and-implementation-status-of-opportunistic-encryption-for-ipsec/) [shortcomings](https://www.mail-archive.com/cryptography@metzdowd.com/msg12325.html) and has failed to gain adoption.

|           | zero configuration | encrypts                                                | works offline | required infrastructure                                                  | post-quantum | protects traffic using existing IPs | secure hostnames | free software         | encrypted transport               |
|-----------|--------------------|---------------------------------------------------------|---------------|--------------------------------------------------------------------------|-----------------------------|-------------------------------------|------------------|-----------------------|-----------------------------------|
| Tailscale |❌                | all traffic to specific IP addresses                    |❌           | coordination server (Amazon-hosted)                                      |❌                         |❌                                 |✔️             | client ✔️ , server❌| WireGuard                         |
| Headscale |❌                | all traffic to specific IP addresses                    |❌           | coordination server (self-hosted)                                        |❌                         |❌                                 |✔️             |✔️                  | WireGuard                         |
| innernet  |❌                | all traffic to specific IP addresses                    |❌           | coordination server                                                      |❌                         |❌                                 |✔️             |✔️                  | WireGuard                         |
| Nebula    |❌                | all traffic to specific IP addresses                    |❌           | certificate authority                                                    |❌                         |❌                                 |✔️             |✔️                  | custom protocol                   |
| MACsec    |❌                | Ethernet traffic between host and switch (not e2ee)     |✔️          | RADIUS server                                                            |❌                         |✔️                                |❌              | host ✔️ , switch❌  | MACsec                            |
| TCPcrypt  |✔️               | TCP traffic between any participating hosts             |✔️          | none                                                                     |❌                         |✔️                                |❌              |✔️                  | TCPCrypt                          |
| IPsec OE  |❌                | all WAN and LAN traffic between participating hosts     |✔️          | DNS+DNSSEC  for authentication with static records and/or third party CA |❌                         | not by default                      |❌              |✔️                  | IPSec's peer-wise common cipher-suite |
| PQWireGuard  |❌                | all WAN and LAN traffic between participating hosts     |✔️          | manual key exchange out of band |✔️                         | not by default                      |❌              |✔️                  | PQWireGuard |
| Vula      |✔️               | all traffic between participating hosts on the same LAN |✔️          | none                                                                     | transitional (passive)                         |✔️                                |✔️             |✔️                  | WireGuard                         |

# Additional projects to analyze?
Please feel free to send us a request to analyze your favorite software and we will add it to the above table.
