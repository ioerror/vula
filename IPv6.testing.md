Testing IPv6 support
====================

From within the `podman` directory, `make clean` followed by `make ping` will
start a test network with two vula peers and send a ping between them using
vula ULA (`fdff:ffff:fffd::/48`) addresses provided by vula name resolution.

Running `make sh` will enter a shell in the first container, where commands
such as `vula peer`, `vula prefs`, etc can be used to observe the test
container's configuration.

FIXME: provide instructions here for testing on real machines. (`make deb`,
install it, ... `ping`? `tcpdump`? `ip route get`?)
