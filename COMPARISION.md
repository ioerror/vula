There are a wide variety of tools which can be used to create end-to-end
encrypted tunnels between hosts, or which share other superficial similarities
with Vula.

To our knowledge, however, none of them share Vula's design goal of providing
fully-automatic end-to-end encryption of local area network traffic.

The following is a list of unique properties which Vula provides:
* No infrastructure required
* Fully automatic: LAN traffic between hosts with Vula installed is protected without any configuration whatsoever
* Works on offline networks (eg, with RFC 3927 link-local addressing on ethernet, ad-hoc wifi, thunderbolt, etc)
* Protects traffic using existing IP addresses (whether DHCP-assigned, link-local, or manually configured)

Projects such as [Tailscale](https://tailscale.com/),
[Headscale](https://github.com/juanfont/headscale), and
[innernet](https://github.com/tonarino/innernet) are similar to Vula in that
they can be used to encrypt traffic between hosts on a LAN using WireGuard
tunnels, but they differ in some important respects:

* They only create tunnels between hosts that are logged in to the same account on a centralized coordination server
    * Tailscale outsources the operation of this component to Amazon, a surveillance actor
    * Headscale and innernet provide free software implementations which can be self-hosted, but remain a single point of failure
* They use a different IP range inside and outside of the tunnels, so LAN-based applications need to be reconfigured to benefit from it.
* They do not provide any post-quantum protection

With the exception of TCPcrypt, the other projects listed all are designed to
protect traffic between hosts which are configured to be part of an
organization, whereas Vula provides automatic encryption of traffic between
*all* locally-reachable hosts that are running it.

TCPcrypt is an outlier, in that it does provide opportunistic encryption
between hosts without any configuration; however, it only protects TCP traffic,
does not provide secure names, and its key verification system requires
application-specific support. These and other deployment impediments have
prevented its adoption.


|           | Fully automatic, zero configuration                                                   | works offline | Required infrastructure             | Transitionally post-quantum | uses existing Ips | secure hostnames | free software | Protects non-TCP protocols | encrypted transport |
|-----------|---------------------------------------------------------------------------------------|---------------|-------------------------------------|-----------------------------|-------------------|------------------|---------------|----------------------------|---------------------|
| Tailscale | Requires login, and only protects traffic between systems in the same organization    | no            | coordination server (Amazon-hosted) | no                          | no                | yes              | partially     | yes                        | WireGuard           |
| Headscale | Requires login, and only protects traffic between systems in the same organization    | no            | coordination server                 | no                          | no                | yes              | yes           | yes                        | WireGuard           |
| Nebula    | Requires manual configuration                                                         | no            | certificate authority               | no                          | no                | yes              | yes           | yes                        | custom protocol     |
| innernet  | Requires manual configuration                                                         | no            | coordination server                 | no                          | no                | yes              | yes           | yes                        | WireGuard           |
| MACsec    | Requires manual configuration                                                         | yes           | RADIUS server                       | no                          | yes               | no               | yes           | yes                        | MACsec (not e2ee)   |
| TCPcrypt  | yes                                                                                   | yes           | none                                | no                          | yes               | no               | yes           | no                         | TCPCrypt            |
| Vula      | yes                                                                                   | yes           | none                                | yes                         | yes               | yes              | yes           | yes                        | WireGuard           |

# Additional projects to analyze?
Please feel free to send us a request to analyze your favorite software and we will add it to the above table.
