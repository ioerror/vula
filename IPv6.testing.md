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
apt update
apt install -y make podman uidmap
```

The test network is driven by a Makefile in the podman directory. To start a
test network and run the tests:

```
cd podman
make test
```

The `test` target will run both the unit tests, and integration tests. You can
also run `make sh` to get a shell in one of the containers.

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
