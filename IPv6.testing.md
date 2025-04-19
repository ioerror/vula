Testing IPv6 support
====================

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

The `test` target will run both the unit tests, and integration tests. You can
also run `make sh` to get a shell in one of the containers.

To run with N containers (instead of the default of `N=2`) you can add N= to
all of the make targets.


```
make clean test N=6
make run cmd="vula status -v" N=6
```

The `sh` target also accepts `i=` to  get a shell in other containers than the
first one. You can start a shell in two containers:
```
make run sh
```
(in another window)
```
make run sh i=2
```
To observe the vula state engine in action, you can run `watch -n 1 vula peer`
in one while you add and remove IPs from your ethernet interface with the `ip`
command in the other container.

## Testing on a real system with other vula peers on the same LAN

First build all of the vula related packages and the vula package from the root
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
command, and see a list of peers using `vula peer`.

## Testing default route encryption

If a vula peer's current default route is via the configured IP of a vula peer,
it will automatically route all internet traffic to it over vula. If the router
is configured to announce its own ULA suffix, and performs NAT or NPTv6 from
these IPs to the internet, vula default gateway encryption will work
automatically.

However, if the network is configured to use public IP addresses, vula will, by
default, not accept these IPs. As a result, IPv6 connectivity will currently be
non-functional if the router is running vula until the clients and router are
not manually configured to have its prefix added to their `subnets_allowed`
preference. We will soon improve this so that unprotected connectivity is not
impaired in the case that a client is not configured to allow a vula-enabled
IPv6 router's prefix.

To test default encryption using public IP addresses, the command to run on
both the gateway and client(s) is:

```
vula prefs add subnets_allowed 2001:db8::/64
```

For the purpose of testing default gateway encryption with public addresses,
one can use an Ubuntu 24.10 computer with ethernet and wifi, where the ethernet
is connected to a gateway that offers prefix delegation (via the DHCPv6 `IA_PD`
option). Ubuntu's "network connection sharing" feature will create an IPv4-only
router by default; the steps to get it to become an IPv6 router (and request a
prefix from its upstream router, and announce it on its wifi interface) is
this:

1. Configure internet sharing from ethernet to wifi using the "create hotspot"
button under Settings -> Wi-Fi.

2. Stop the hotspot

3. Locate the netplan YAML file where the Network Manager configuration is stored:
```
grep -rl access-points /etc/netplan/
```

4. Edit this file to add `ipv6.method: "shared"` to the `passthrough` section
underneath `networkmanager` under `access-points`.

5. Re-enable the hotspot, and confirm that other computers can connect through
it using the public IPv6 addresses it is announcing.

In this configuration, if the router is also running vula, vula-enabled clients
will use it as their default route for both v4 and v6 but will not be able to
get online because vula's default `subnets_allowed` prevents the public IPs
from being added to the `allowsed-ips` list. To enable this, first determine
the prefix the addresses are in using `ip -6 route`. Add this prefix to vula
using the command `vula prefs add subnets_allowed` on both the gateway and
client device.

At this point, IPv6 connectivity should be restored. You can confirm that your
packets are going over vula using `ip route get`, `tcpdump`, etc.

TODO for these instructions:

* describe how to configure a gateway using ULAs, which vula can use automatically
* test v6-only client and gateway with public addresses
