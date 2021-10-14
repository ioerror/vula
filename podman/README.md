This directory contains a Makefile with various targets which use podman to
package, test, and deploy vula. This allows developers to work on the software
without needing to install anything on their system besides `podman`, `sudo`,
and `make`.

Most of these make targets require sudo to obtain the `CAP_NET_ADMIN`, and will
thus prompt for a password. The make command itself should be run as an
unprivileged user.

## Packaging

### `make deb`

This target will use Debian bullseye to build a `.deb` package of vula in
`../deb_dist/` using the current checkout (including any uncomitted changes).
It does not require root to run.

### Other OS packages

It would be nice to have make targets for creating packages for other operating
systems here.

## Test network

### `make test`

This will create a `vula-net` podman internal network, run
vula in two containers connected to that network, and send a ping between them.
It will also run the pytest test suite in one of them. Running it again will
re-run the pytest and ping, but will not restart the services in the
containers.

More advanced integration tests using podman should be implemented here,
such as creating a router container which is in the internal network and also
internet connected to test default route encryption functionality.

### `make retest`

This will stop and restart the testnet containers, and re-run `make test`.

### `make testnet-shell`

This will launch a shell in the first testnet container.

### `make testnet-clean`

This will stop and delete the testnet containers.

### `make test-all`

This will currently run these commands:
```
make dist=hirsute testnet-clean test
make dist=bullseye testnet-clean test
make dist=impish testnet-clean test
```
..which will run the test network with each of the three distributions where
tests currently pass. `dist=buster` and `dist=focal` are also supported, but
are not currently working.

## Running vula on the host's LAN

### `make lan-start`

This will create a new podman container (as root) called `vula` with `host`
networking, meaning that it will operate in the default network namespace. This
is a convenient way that one can run vula to communicate with other hosts on
their physical LAN, without needing to install any dependencies besides
`wireguard`, `podman`, `make`, and `sudo`.

### `make lan-shell`

This will spawn a shell in the `vula` container started by `lan-start`.

### `make lan-stop`

This will stop the `vula` container started by `lan-start`.

### `make lan-clean`

This will delete the `vula` container started by `lan-start`.

## Development mode

The `test-*` and `lan-*` make targets both have the side effect of creating a
podman image called `vula-$dist` (bullseye, by default), which by default
contains a dpkg installation of vula. This image can be modified or replaced.

### `make editable-image`

This target will replace the `vula-$dist` image with one where vula is is
installed in editable mode (eg, `python setup.py develop`). This will not
affect containers created prior to this target being run, so, in practice you
might want to prefix it with `clean`. **This is currently semi-broken.** The
resulting image currently runs vula from the local checkout in the
testnet-shell, but for some reason systemd is continuing to use the
deb-installed version. So, for now it is still necessary to run `make clean
test` to rebuild a new image to test new changes. This is still quite fast,
however, as the deps image is not removed by `make clean`.

## Cleaning up

### `make clean`

This will delete the `.deb` package built in `../deb_dist`, the `vula-$dist`
podman images, the test containers, and any stray intermediate containers. It
will *not* delete the `vula-deps-$dist` images, which require network access to
recreate, nor will it delete the `vula` container which is created by the
`lan-start` target.

### `make clean-all`

This will delete all vula-related podman containers, including `vula`, and all
images, including `vula-deps-$dist`, as well as the `vula-net` podman network
and the `.deb` package in `../deb_dist/`.
