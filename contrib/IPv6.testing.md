Testing IPv6 support
====================

Please refer to `vula/contrib/README.ipv6.overview.md` to understand the IPv6
feature branch.

Testing the `ipv6` branch is possible using podman and as well by building
packages and installing vula on a normal Ubuntu 24.10 system. Other systems are
also possible, but some distributions lack certain dependencies.

## Check out code

```
git clone https://www.codeberg.org/vula/vula/
cd vula/
git checkout ipv6
```

### Containerized tests with `podman`

The dependencies required for running a podman test network on Ubuntu 24.10 are
simply:

```
sudo apt update
sudo apt install -y make podman uidmap
```

The test network is driven by a Makefile in the podman directory. To start a
test network and run the tests:

```
cd podman
make test
```

The `test` target will run both the unit tests and integration tests. You can
also run `make sh` to get a shell in one of the containers, and when you're
done `make stop` to stop them and `make clean-all` to remove the podman images
it creates.

To run with N containers (instead of the default of `N=2`) you can add `N=` to
all of the make targets which involve multiple containers.

```
$ make N=5 clean test
```
```
$ make run cmd="vula status -v" N=1
# running "vula status -v" on 1 hosts
# podman exec -it vula-bookworm-test1 vula status -v
[ active ] vula-publish.service                (0:00:38)
[ active ] vula-discover.service               (0:00:42)
[ active ] vula-organize.service               (0:00:46)
[ active ] local.vula.organize dbus service (running repair --dry-run)
[ active ] Publishing on eth0: fe80::c69:f9ff:fe4b:e0b9, fd54:f27a:17c1:3a61::2, 10.89.0.2
[ active ] 4 enabled peers correctly configured; 0 disabled
[ active ] vula-bookworm-test1.local.'s vula ULA is fdff:ffff:ffdf:5a51:f134:b2e9:8baf:d952
```
```
$ make run cmd="vula peer" N=1
# running "vula peer" on 1 hosts
# podman exec -it vula-bookworm-test1 vula peer
peer: vula-bookworm-test2.local.
  id: XXto6t0g0HufO2ZdiMZT8l3W9Y57kKpBE9nj0bEB1E8=
  status: enabled unpinned unverified
  endpoint: [fe80::7cf3:92ff:fe58:53de]:5354
  primary ip: fdff:ffff:ffdf:dda:efda:c76b:7f12:2735
  allowed ips: fdff:ffff:ffdf:dda:efda:c76b:7f12:2735/128, fd54:f27a:17c1:3a61::3/128, 10.89.0.3/32
  latest signature: 0:01:32 ago
  latest handshake: 0:01:11 ago
  transfer: 236 B received, 324 B sent
  wg pubkey: l7gw8UzhoYx9u0sWkGtXRgLP766+tcsox3YENbQ/83k=

peer: vula-bookworm-test3.local.
  id: BCeZ0pMpJpSlv1xl3Pd2MaMI1zHEIcAE9rmLoXQ6C9Y=
  status: enabled unpinned unverified
  endpoint: [fe80::54e3:4ff:fe15:66ca]:5354
  primary ip: fdff:ffff:ffdf:e502:f69d:d711:2d98:f672
  allowed ips: fdff:ffff:ffdf:e502:f69d:d711:2d98:f672/128, fd54:f27a:17c1:3a61::4/128, 10.89.0.4/32
  latest signature: 0:01:30 ago
  latest handshake: 0:01:11 ago
  transfer: 236 B received, 324 B sent
  wg pubkey: 0FsmcIMCld+auN/u0WvA8kumJItSXi+Ia1gklTZNHTM=

peer: vula-bookworm-test4.local.
  id: kJhdm4CXaXK3pZAKlMaxlb8OQdBW+1upnbtLSr9dQdM=
  status: enabled unpinned unverified
  endpoint: [fe80::d49a:1fff:fe65:a00e]:5354
  primary ip: fdff:ffff:ffdf:397d:5b16:7625:4db5:20
  allowed ips: fdff:ffff:ffdf:397d:5b16:7625:4db5:20/128, fd54:f27a:17c1:3a61::5/128, 10.89.0.5/32
  latest signature: 0:01:30 ago
  latest handshake: 0:01:10 ago
  transfer: 236 B received, 324 B sent
  wg pubkey: SU5AcYfCL5na9ZT3O7Skh8kuJwg9fs+KNvcJDDQvtDg=

peer: vula-bookworm-test5.local.
  id: C+QctiYllHgwT2HWZgmqK017GnbyM1HlGiD2strJNBY=
  status: enabled unpinned unverified
  endpoint: [fe80::98b1:a5ff:fe56:179e]:5354
  primary ip: fdff:ffff:ffdf:3ddb:6dec:e966:7238:ac02
  allowed ips: fdff:ffff:ffdf:3ddb:6dec:e966:7238:ac02/128, fd54:f27a:17c1:3a61::6/128, 10.89.0.6/32
  latest signature: 0:01:28 ago
  latest handshake: 0:01:10 ago
  transfer: 236 B received, 324 B sent
  wg pubkey: f/UwEfPfLBVYUvsOfEXB0NUOUGLshPSSthCo16Gk+iU=
```

The `sh` target also accepts `i=` to  get a shell in containers other than the
first one. You can start a shell in two containers:
```
make sh
```
(in another window)
```
make sh i=2
```
To observe the vula state engine in action, you can run `watch -n 1 vula peer`
in one container while you add and remove IPs from your ethernet interface with
the `ip` command in the other container with commands like these:

```
ip addr add dev eth0 fd54:f27a:17c1:3a61::2
ip addr del dev eth0 fd54:f27a:17c1:3a61::2
```

As you remove and re-add the podman-assigned ULA from one container, you can
see in the other container running `watch -n 1 vula peer` that the peer's
allowed IPs are changing to reflect its new descriptors it is publishing after
each change.

## Testing on a real system with other vula peers on the same LAN

First, build all of the vula related packages and the vula package from the root
of the git repository:
```
# build debs:
./misc/quick-build.sh
# install dependencies:
sudo dpkg -i ggwave/dist/libggwave-dev_0.4.2_amd64.deb
sudo dpkg -i ggwave/dist/python3-ggwave_0.4.2-0_amd64.deb
sudo dpkg -i highctidh/dist/python3-highctidh_1.0.2024092800-1_amd64.deb
sudo dpkg -i pymonocypher/dist/python3-pymonocypher_4.0.2.5-0_amd64.deb
sudo dpkg -i reunion/dist/python3-rendez_1.2.1-1_all.deb
sudo dpkg -i vula_libnss/dist/python3-vula-libnss_0.0.2024120900-1_amd64.deb
# install vula:
sudo dpkg -i dist/python3-vula_0.2.2025040600-1_all.deb
```
Once vula is installed, you can check its status using the `vula status`
command, and see a list of peers with `vula peer`.

The examples below show output from a podman test container (using `make sh` as
described above). You can run the same commands on a real system using your
peers' hostnames to confirm similar output.

```
root@vula-bookworm-test1:~/vula# vula status
[ active ] vula-publish.service                (0:15:29)
[ active ] vula-discover.service               (0:15:33)
[ active ] vula-organize.service               (0:15:36)
[ active ] local.vula.organize dbus service (running repair --dry-run)
[ active ] Publishing 3 IPs on eth0
[ active ] 1 enabled peers correctly configured; 0 disabled
[ active ] vula-bookworm-test1.local.'s vula ULA is fdff:ffff:ffdf:e3bf:2e05:d70f:d2f7:1fde
```

```
root@vula-bookworm-test1:~/vula# vula peer
peer: vula-bookworm-test2.local.
  id: 06IEe9qeL9rkfrN9tYbfTDZbu6ihDkZ1SXpe7nDgYpE=
  status: enabled unpinned unverified
  endpoint: [fe80::38b0:80ff:fef7:ec9f]:5354
  primary ip: fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa
  allowed ips: fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa/128, fd54:f27a:17c1:3a61::3/128, 10.89.0.3/32
  latest signature: 0:38:49 ago
  latest handshake: 0:28:17 ago
  transfer: 508 B received, 596 B sent
  wg pubkey: qvhMODx7aoHkU/t2ATcks+SRYavnjNvk/qMFlvG4hTw=
```

Applications which use glibc to resolve peer names ending with the suffix
`local.` will receive peer's vula-generated IPv6 addresses in our
fdff:ffff:fffd::/48 block via our libnss plugin without using DNS.

You can query nssswitch's host resolution manually to confirm vula IPs are
being provided from it:
```
root@vula-bookworm-test1:~/vula# getent ahostsv6 vula-bookworm-test2.local.
fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa STREAM vula-bookworm-test2.local.
fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa DGRAM
fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa RAW
root@vula-bookworm-test1:~/vula# getent ahostsv4 vula-bookworm-test2.local.
10.89.0.3       STREAM vula-bookworm-test2.local.
10.89.0.3       DGRAM
10.89.0.3       RAW
```

You can confirm connectivity using these addresses using the ping command:

```
root@vula-bookworm-test1:~/vula# ping6 -c 1 vula-bookworm-test2.local.
PING vula-bookworm-test2.local.(vula-bookworm-test2.local. (fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa)) 56 data bytes
64 bytes from vula-bookworm-test2.local. (fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa): icmp_seq=1 ttl=64 time=0.144 ms

--- vula-bookworm-test2.local. ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.144/0.144/0.144/0.000 ms
```

You can confirm an IPv4 name resolution for the name-with-dot returns peers' IPv4 addresses:
```
root@vula-bookworm-test1:~/vula# ping -4 -c 1 vula-bookworm-test2.local.
PING  (10.89.0.3) 56(84) bytes of data.
64 bytes from vula-bookworm-test2.local. (10.89.0.3): icmp_seq=1 ttl=64 time=1.17 ms

---  ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 1.170/1.170/1.170/0.000 ms
```

You can use the `ip route get` command to see how packets to a given
destination will be routed:

```
root@vula-bookworm-test1:~/vula# ip route get 10.89.0.3
10.89.0.3 dev vula table 666 src 10.89.0.2 uid 0
    cache
root@vula-bookworm-test1:~/vula# ip route get fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa
fdff:ffff:ffdf:2428:7c68:40e8:c2ad:bafa from :: dev vula table 666 proto static src fdff:ffff:ffdf:e3bf:2e05:d70f:d2f7:1fde metric 1024 pref medium
```

In the example above, there are also existing ULAs (RFC 4193 Unique Local
Addresses) which have been assigned by podman. You can confirm that traffic
between these IPs is also protected by vula:
```
root@vula-bookworm-test1:~/vula# ip route get fd54:f27a:17c1:3a61::3
fd54:f27a:17c1:3a61::3 from :: dev vula table 666 proto static src fd54:f27a:17c1:3a61::2 metric 1024 pref medium

```

## Testing default route encryption

The original vula IPv4 default route encryption continues to work and the
`ipv6` branch enhancements bring a similar IPv6 default route encryption
enhancement to vula.

If a vula peer's current default route for IPv4 is through an IPv4 IP of a vula
peer, it will automatically route all internet IPv4 traffic via that peer over
its vula interface. If the vula peer acting as a gateway is performing IPv4 NAT
for vula peers on the local-area network for vula peers with RFC1918 or IPv4
link-local addresses, vula's default gateway encryption will work
automatically.

If a vula peer's current default route for IPv6 is through an IPv6 IP of a vula
peer, it will automatically route all internet IPv6 traffic via that peer over
its vula interface. If the vula peer acting as a gateway is configured to
announce its own ULA suffix, and the vula peer acting as a gateway performs
NPTv6 from these IPs to the internet, vula's default gateway encryption will
work automatically. It is additionally possible with only one IPv6 address on
the vula peer acting as a gateway to use IPv6 NAT66 though NPTv6 is generally
considered the prefered method of internet sharing with IPv6.

With a properly configured IPv6 enabled Ubuntu 24.10 system, a gateway should
have at least one public IPv6 address or ideally an IPv6 prefix that is large
enough to perform NPTv6 on all of the hosts on the local-area network.
Configuring a full Ubuntu 24.10 system as an IPv4/IPv6 router with upstream
public IPv6 addresses and downstream ULA prefix advertisements is out of scope
for this document. As an example, the vula peer acting as a gateway for a
local-area network of vula peers announces the ULA of `fdfd:deed:dfdf::/64` on
its `internal` interface and it has one or more public IPs on its `external`
interface.

One vula peer may act as a gateway for both IPv4 and IPv6.

### Default route encryption using network assigned ULAs

When vula is present on a network that announces ULAs within the `fc00::/7`
IPv6 address space and performs NAT66 or NPTv6 works automatically

As an example we show the `vula peer` command listing current peers and if a
vula peer is acting as your gateway, the status line for the peer will include
the string `gateway`. Showing the example of ```vula peer|grep -A 7 -B 2
gateway```:
```
peer: apu4d4.local.
  id: Yr1NcQZpSe+JY2b9+/4BM5b6X6/yN4JzTnmUnxUDhCw=
  status: enabled unpinned unverified gateway
  endpoint: [fe80::20d:b9ff:fe59:e570]:5354
  primary ip: fdff:ffff:ffdf:7e3d:113c:6d4e:812a:9ec7
  allowed ips: fdff:ffff:ffdf:7e3d:113c:6d4e:812a:9ec7/128, fdfd:deed:df00:0:20d:b9ff:fe59:e570/128, 192.168.2.1/32, 0.0.0.0/0, ::/0
  latest signature: 5:23:36 ago
  latest handshake: 0:00:33 ago
  transfer: 5.42 GiB received, 3.18 GiB sent
  wg pubkey: 56BndBP+S8owAw9Rgmt5GcoM08Sl0fbmYrtZ+t+r0Ew=
```

Checking the route of a public IPv4 address will show that it is routed through
the `vula` device:
```
ip route get 62.176.231.184
62.176.231.184 dev vula src 192.168.2.24 uid 1001 
```

For informational purposes, we provide an ip6tables NAT66 example with ethernet
interfaces `internal` and `external`:
```
# Outbound (LAN -> Internet): map ULA -> public address
ip6tables -t nat -A POSTROUTING -o external -j MASQUERADE
# Inbound (Internet -> LAN): map public -> ULA
ip6tables -A FORWARD -i external -o internal -m state --state RELATED,ESTABLISHED -j ACCEPT
ip6tables -A FORWARD -i internal -o external -j ACCEPT
```

For informational purposes, we also provide an ip6tables NPTv6 example with
ethernet interfaces `internal` and `external` to translate between ULA prefix
`fdfd:deed:dfdf::/64` and an example public IPv6:
```
# Outbound (LAN -> Internet): map ULA -> public prefix
ip6tables -t nat -A POSTROUTING \
  -s fdfd:deed:dfdf::/64 \
  -o external \
  -j NETMAP --to 2001:db8::/64

# Inbound (Internet -> LAN): map public prefix -> ULA
ip6tables -t nat -A PREROUTING \
  -d 2001:db8::/64 \
  -i external \
  -j NETMAP --to fdfd:deed:dfdf::/64
```

Additional `ip6tables` or `nft` policy rules are certainly required for
firewalling and other forwarding configuration.

# Experimental IPv6 addresses

The vula project does not encourage using IPv4 public addresses or IPv6 public
addresses directly, without NPTv6 or NAT66, as signifigant design and security
analysis remains.  Using public IPv6 (or IPv4) addresses may be unsafe in ways
that we have not specified. This is a footgun that we have included for risk
taking experimenters who wish to provide us feedback in the future design of
such a possible feature enhancemnet.

IPv6 public address connectivity requires that a vula peer acting as a gateway
manually be configured with public IPv6 address prefixes. The vula peers using
the vula peer acting as a gateway must be manually configured to have the same
public IPv6 prefix added to their `subnets_allowed` preference.

For the purpose of testing default gateway encryption with public addresses,
one can use an Ubuntu 24.10 computer with ethernet and wifi, where the ethernet
is connected to a gateway which offers prefix delegation (via the DHCPv6 `IA_PD`
option). Ubuntu's "network connection sharing" feature will create an IPv4-only
router by default; the steps to get it to become an IPv6 router (and request a
prefix from its upstream router, and announce it on its wifi interface) are as
follows:

1. Configure internet sharing from ethernet to wifi using the "create hotspot"
button under Settings -> Wi-Fi.

2. Stop the hotspot

3. Run `grep -rl access-points /etc/netplan/` to locate the netplan YAML file
where the Network Manager hotspot configuration is stored.

4. Edit this file to add `ipv6.method: "shared"` to the `passthrough` section
underneath `networkmanager` under `access-points`. (This change causes Network
Manager to request a prefix delegation via DHCPv6 from its other interface,
from which it will announce addresses on the hotspot.)

5. Re-enable the hotspot, and confirm that other computers can connect through
it using the public IPv6 addresses it is announcing.

In this configuration, if the Ubuntu hotspot is also running vula, vula-enabled
clients will use it as their default route for both v4 and v6 *but* they will
not be able to actually get online because vula's default `subnets_allowed`
prevents the public IPs from being added to the `allowsed-ips` list. To enable
connectivity using public addresses, determine the prefix the addresses are in
using `ip -6 route` and then add this prefix to vula using the command
`vula prefs add subnets_allowed 2001:db8::/64` (with your own subnet) on both
the gateway and client device. Connectivity should then be restored, with all
internet-bound traffic routed over the vula device.

You can confirm that a peer is configured as the gateway using the `vula peer`
command. A peer which is the current gateway will have the string "gateway"
included in its status line, and will have default routes included in its
allowed-ips.

This example is from a system with `2a00:1f:6f58:72bd::/64` in its
`subnets_allowed`:

```
$ vula peer
peer: ubuntu-router.local.
  id: At0ya5C/VNGLL3XNeaSBnY3PAl3UiMydzqCtS2WDopU=
  status: enabled unpinned unverified gateway
  endpoint: [fe80::f690:e486:b85:794e]:5354
  primary ip: fdff:ffff:ffdf:142a:c9cf:406c:c4ac:8bc5
  allowed ips: fdff:ffff:ffdf:142a:c9cf:406c:c4ac:8bc5/128, 2a00:1f:6f58:72bd::1/128, 10.42.0.1/32, 0.0.0.0/0, ::/0
  latest signature: 3:32:30 ago
  latest handshake: 0:01:51 ago
  transfer: 1.39 GiB received, 1.07 GiB sent
  wg pubkey: 32P7hYDgRxWMJieYbPXGKuNH+UkAtMYXNIthaPTk9RU=
```

Using a vula-enabled gateway, you can confirm that your route to internet
destinations is via the vula device and is using the same source address as it
would without vula. This example is from a system with `2a00:1f:6f58:72bd::/64`
in its `subnets_allowed` (which its vula-enabled gateway also has):

```
$ ip route get 2a01:584:31::1
2a01:584:31::1 from :: dev vula proto static src 2a00:1f:6f58:72bd:762:a121:38d2:fe41 metric 1024 pref medium
$ ip route get 185.15.59.224
185.15.59.224 dev vula src 10.42.0.162 uid 1000
    cache
```

Finally, after reconnecting to a different network where the vula gateway is no
longer the default gateway, you can confirm that the `vula peer` command no
longer lists it as the gateway.
