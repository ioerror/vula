This directory contains a Makefile with various commands which use podman to
package, test, and deploy vula. This allows developers to work on the software
without needing to install anything on their system besides `podman`, `sudo`,
and `make`. It is also a possible way to deploy vula on systems where some
dependencies are unavailable.

Most of these make targets require sudo to obtain the `CAP_NET_ADMIN`, and will
thus prompt for a password. The make command itself should be run as an
unprivileged user.

To use these commands, you must first git clone the repo and cd in to the
`podman` directory:

```
git clone https://codeberg.org/vula/vula
cd vula/podman
make
```

Running `make` with no arguments will print this README and some configuration
variables.

## Distributions

This Makefile accepts a `dist` argument specifying which Linux distribution to
use. Distributions listed in **bold** in the table below are "enabled" by
default; that is, they are in the default value of the `dists` argument.
Therefore, they will be operated on by make targets with `-all` in their name.
If you use a different distribution which is not in the default `dists` list,
you can cleanup afterwards by specify it as the `dists` argument to the `make
clean` target.


| dist         | name             | pytest | ping test | PyPI packages required                                      | notes                                                                           |
|--------------|------------------|--------|-----------|-------------------------------------------------------------|---------------------------------------------------------------------------------|
| buster       | Debian 10        | ❌     | ❌        | sibc, vula\_libnss, stdeb, zeroconf, pyroute2, cryptography | conflicts with python3-cryptography, pyyaml, etc are not easily solved with pip |
| focal        | Ubuntu 20.04 LTS | ✅     | ❌        | sibc, vula\_libnss, stdeb                                   | No multicast connectivity in podman containers                                  |
| hirsute      | Ubuntu 21.04     | ✅     | ✅        | sibc, vula\_libnss                                          |                                                                                 |
| **bullseye** | Debian 11        | ✅     | ✅        | sibc, vula\_libnss                                          |                                                                                 |
| **impish**   | Ubuntu 21.10     | ✅     | ✅        | sibc, vula\_libnss                                          |                                                                                 |
| **fedora34** | Fedora 34        | ✅     | ✅        | sibc, vula\_libnss, pyroute2==0.5.14, pynacl                | manual setup required                                                           |
| alpine       | alpine:latest    | ✅     | ❌        | sibc, vula\_libnss, pyroute2==0.5.14                        | TODO                                                                            |

## Packaging

### `make deb`

This target will build a `.deb` package of vula in `../deb_dist/` using the
current checkout (including any uncommitted changes). It does not require root
to run. By default, it will build using Debian `bullseye`; to build a deb using
Ubuntu `impish` instead you can run `make clean deb dist=impish`.

### `make rpm`

This target will build an RPM using Fedora 34. Note that this package is only
minimally tested and does not yet automatically configure the system; see
[`INSTALL.md`](https://codeberg.org/vula/vula/src/branch/main/podman/INSTALL.md)
for details.

## Test network

### `make dist=bullseye test`

This will create a `vula-net` podman internal network, run vula in two
containers connected to that network, and send a ping between them.  It will
also run the pytest test suite in one of them. Running it again will re-run the
pytest and ping, but will not restart the services in the containers.

More advanced integration tests using podman should be implemented here,
such as creating a router container which is in the internal network and also
internet connected to test default route encryption functionality.

The `dist=bullseye` argument can be omitted; `bullseye` is the default dist.

### `make retest`

This will stop and restart the testnet containers, and re-run `make test`.

### `make testnet-shell`

This will launch a shell in the first testnet container.

### `make testnet-clean`

This will stop and delete the testnet containers for the default distribution
(`bullseye`), or another if specified with `dist=`.

### `make testnet-clean-all`

This will stop and delete the testnet containers for all of the configured
distributions. This is called by `make clean`.

### `make test-all-separate`

This will run the `test` command followed by `testnet-clean` for each `dist` in
`dists`.

### `make test-all`

This will run `make test` for each `dist` in `dists`, but without stopping in
between. Therefore, if you run `make testnet-shell` afterwards, you will be
able to run `vula peer` and see many peers.

### `make systemd-shell`

This will create a new container which, unlike the test hosts created by the
test target, is connected to both the normal `podman` network (online behind
NAT) *and* to the `vula-net` internal network which test hosts are connected
to. Shells and tests for different dists can be run concurrently and
communicate with each other; if a clean test network is desired one can run
`make clean` or `make testnet-clean` prior to running `make test`.

This example will create two test containers for each of three dists, and then
spawn a shell from which six peers should (eventually) be visible when running
`vula peer`:
```
make dist=bullseye test
make dist=hirsute test
make dist=impish test
make dist=bullseye systemd-shell
```
## Vula Man-in-the-Middle Testing

For details: [Vula Man-in-the-Middle Testing Notes](./Vula-MitM-tool.md)

### Usage

Go into the podman directory
```cd podman```

To run the passive adversary test:
```make test-passive-adversary```

To run the active adversary test:
```make test-active-adversary```

Clean everything up
```make clean-sudo```

### If it does not work as expected...
* Due to network issues, sometimes tests will fail on the first run. Re-run the same test.
* If you get lost in podman and stuff, here are some commands that might help.
  * ```sudo podman ps -a```
  * ```sudo podman image ls```
  * ```sudo podman rmi vula-mallory-bullseye```
  * ```sudo podman rm mallory``` 
  * ```sudo podman rm sudo podman rm vula-bullseye-test1``` 
  * ```sudo podman rm sudo podman rm vula-bullseye-test2```
  * ```sudo podman image rm vula-mallory-bullseye```
  * ```sudo podman network ls```
  * ```sudo podman exec -it mallory sh```
  * ```sudo podman image rm <25d0f69960f4> <09a2dc334328> <d40c1669cc17>```
  * ```sudo podman network rm vula-net```
* Checkout 'Comments and known bugs' in [mitm readme](./Vula-MitM-tool.md)


## Development mode

The `test-*` make targets have the side effect of creating a podman image
called `vula-$dist` (bullseye, by default), which by default contains a dpkg
installation of vula. This image can be modified or replaced.

### `make editable-image`

This target will replace the `vula-$dist` image with one where vula is is
installed in "editable mode" using `python setup.py develop`, rather than via a
deb or RPM package. This will not affect containers created prior to this
target being run, so, in practice you might want to prefix it with `clean`. To
go back to using a package-installed image, use `make clean dpkg-image` or `make
clean rpm-image`.

## Cleaning up

### `make clean`

This will delete the `.deb` package built in `../deb_dist`, the `vula-$dist`
podman images, the test containers, and any stray intermediate containers. It
will *not* delete the `vula-deps-$dist` images, which require network access to
recreate.

### `make clean-all`

This will delete all vula-related podman containers for the current set of
`dists`, including the `vula` image for LAN use, and all images, including
`vula-deps-$dist`, as well as the `vula-net` podman network and the `.deb`
package in `../deb_dist/`.

If you have run `make` commands using `dist` arguments which are not in the
default `dists` list, you can also specify them here to clean up after them,
like this:

```
make "dists=buster focal hirsute bullseye impish fedora34 alpine" clean-all
```

