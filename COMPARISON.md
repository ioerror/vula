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

IPsec OE also is designed to provide opportunistic encryption, but has numerous shortcomings and has failed to gain adoption.

|           | zero configuration | encrypts                                                | works offline | Required infrastructure                                                  | Transitionally post-quantum | protects traffic using existing IPs | secure hostnames | free software         | encrypted transport               |
|-----------|--------------------|---------------------------------------------------------|---------------|--------------------------------------------------------------------------|-----------------------------|-------------------------------------|------------------|-----------------------|-----------------------------------|
| Tailscale | no                 | all traffic to specific IP addresses                    | no            | coordination server (Amazon-hosted)                                      | no                          | no                                  | yes              | client yes, server no | WireGuard                         |
| Headscale | no                 | all traffic to specific IP addresses                    | no            | coordination server                                                      | no                          | no                                  | yes              | yes                   | WireGuard                         |
| innernet  | no                 | all traffic to specific IP addresses                    | no            | coordination server                                                      | no                          | no                                  | yes              | yes                   | WireGuard                         |
| Nebula    | no                 | all traffic to specific IP addresses                    | no            | certificate authority                                                    | no                          | no                                  | yes              | yes                   | custom protocol                   |
| MACsec    | no                 | Ethernet traffic between host and switch (not e2ee)     | yes           | RADIUS server                                                            | no                          | yes                                 | no               | host yes, switch no   | MACsec                            |
| TCPcrypt  | yes                | TCP traffic between any participating hosts             | yes           | none                                                                     | no                          | yes                                 | no               | yes                   | TCPCrypt                          |
| IPsec OE  | no                 | all WAN and LAN traffic between participating hosts     | yes           | DNS+DNSSEC  for authentication with static records and/or third party CA | no                          | not by default                      | no               | yes                   | IPSec's lowest common denominator |
| Vula      | yes                | all traffic between participating hosts on the same LAN | yes           | none                                                                     | yes                         | yes                                 | yes              | yes                   | WireGuard                         |

# Additional projects to analyze?
Please feel free to send us a request to analyze your favorite software and we will add it to the above table.
