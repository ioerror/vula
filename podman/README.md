This directory contains a Makefile with various targets which use podman to
package, test, and deploy vula. This allows developers to work on the software
without needing to install anything on their system besides `podman` and
`make`.

Most of these make targets use sudo to obtain `CAP_NET_ADMIN`, and will thus
prompt for a password. The make command itself should be run as an
unprivileged user, however.

## Packaging

### `make deb`

This is the default target. It does not require root to run. It will use Debian
bullseye to build a `.deb` package of vula in `../deb_dist/`.

### Other OS packages

It would be nice to have make targets for creating packages for other operating
systems here.

## Test network

### `make test`

This will create a `vula-net` podman internal network, run
vula in two containers connected to that network, and send a ping between them.

More advanced integration tests using podman should be implemented here,
such as creating a router container which is in the internal network and also
internet connected to test default route encryption functionality.

### `make testnet-shell`

This will launch a shell in the first testnet container.

## Running vula on the host's LAN

### `make lan-start`

This will create a new podman container (as root) called `vula` in the `host`
namespace. This is a convenient way that one can run vula to communicate with
other hosts on their physical lan, without needing to install any dependencies
besides `podman`, `make`, and `sudo`.

### `make lan-shell`

This will spawn a shell in the `vula` container started by `lan-start`.

### `make lan-stop`

This will stop the `vula` container started by `lan-start`.

### `make lan-clean`

This will delete the `vula` container started by `lan-start`.
