---
title: "Install"
date: 2021-08-04T17:16:15+02:00
draft: false
---

# Requirements

Currently, GNU/Linux is the only supported operating system. We plan to port
the software to other operating systems in the future.

The software has been developed and tested on Debian (bullseye), Mobian, and
Ubuntu (20.04 and 20.10). It is likely to work on other modern systemd-based
distributions.

Vula can also be run without systemd, and/or in a single monolithic process,
but how to do so is not yet documented.

We do not yet offer packages for download, but you can build your own deb or
wheel from a git checkout.

# Install

## option 0: quick install

For a simple technology demonstration we offer an insecure quick install (eg: a dangerous [curl
pipe sudo
bash](https://www.idontplaydarts.com/2016/04/detecting-curl-pipe-bash-server-side/))
process:

* `cd /dev/shm && wget https://codeberg.org/vula/vula/raw/branch/main/misc/quick-install.sh`
* `bash quick-install.sh`

## option 1: manually build and install Debian Packages

* `sudo apt install --no-install-recommends wireguard wireguard-tools python3-yaml python3-click python3-nacl python3-schema python3-pip python3-pydbus python3-pyroute2 python3-pytest-runner python3-pytest python3-toml python3-py python3-packaging python3-pluggy python3-hkdf python3-ifaddr python3-cryptography python3-dbus python3-pygments python3-systemd python3-qrcode python3-all python-all fakeroot build-essential dh-python debhelper make gcc python3-all-dev python3-zeroconf`
* `sudo pip3 install stdeb sibc` (note: unfortunately this step still requires installing stdeb, sibc, and its dependencies with pip as root - you can alternately build a deb of `sibc` but this procedure is not yet documented here. the stdeb version from Debian stable and Ubuntu 20.10 is insufficient, however.)
* `git clone --recurse-submodules https://codeberg.org/vula/vula_libnss`
* `cd vula_libnss`
* `make deb && sudo dpkg -i deb_dist/python3-vula-libnss_*.deb`
* `cd ../`
* `git clone https://codeberg.org/vula/vula`
* `cd vula`
* `make deb && sudo dpkg -i deb_dist/python3-vula_*_all.deb`

Installing the deb will automatically configure `nsswitch`, restart
`systemd-sysusers`, reload `dbus`, etc, and will tell `systemd` to enable and
start the `vula-organize` service.

## option 2: build a wheel and install with pip

This option is available for advanced technical users - it requires manual
setup of `[vula_libnss](https://codeberg.org/vula/vula_libnss)` after
installing `vula_libnss`. This essentially means ensuring that the libnss
shared object file is installed in `/lib/libnss_vula.so.2`. This may be
installed by building a Debian package or by installing `vula_libnss` with pip
and manually copying the `libnss_vula.so.2` file from inside the installed
location to the correct location on the system.

If you don't mind installing many things using `sudo pip`, the software can be installed this way:

* `git clone --recurse-submodules https://codeberg.org/vula/vula`
* `cd vula`
* `sudo pip install .`

After installing with pip, users will need to configure the system:
* `sudo vula configure nsswitch`
* `sudo systemctl daemon-reload`
* `sudo systemctl restart systemd-sysusers`
* `sudo systemctl reload dbus`
* `sudo systemctl enable --now vula-organize`

# Running vula

To see the current status:
* `vula`

To start vula (via dbus activation) if it is not started, or print the status
if it is:
* `vula start`

To see a list of subcommands:
* `vula --help`

To see a list of peers:
* `vula peer`

To see a list of commands for working with peers:
* `vula peer --help`

To see a list of peers, including disabled peers:
* `vula peer show --all`

To see descriptors and qrcodes for all enabled peers:
* `vula peer show -Dq`

To see the preferences:
* `vula prefs`

To see commands for editing preferences:
* `vula prefs --help`

More documentation is coming soon.

