---
title: "Install"
date: 2025-03-20T14:14:30+01:00
draft: false
---

# Requirements

Currently, GNU/Linux is the only supported operating system. We plan to port
the software to other operating systems in the future.

The software has been developed and tested on Debian (bullseye), Mobian, and
Ubuntu (20.04 and 20.10). It is likely to work on other modern systemd-based
distributions. Option 0 is likely to only work on Debian testing and the latest
Ubuntu distro.

Vula can also be run without systemd, and/or in a single monolithic process,
but how to do so is not yet documented.

We do not yet offer packages for download, but you can build your own deb or
wheel from a git checkout.

# Install

## option 0: quick install

For a simple technology demonstration we offer an insecure quick package
building script to aid in installing vula:

* `cd /dev/shm && git clone https://codeberg.org/vula/vula/`
* `cd vula`
* `./misc/quick-install.sh`

Install the newly built Debian packages.

## option 1: manually build and install Debian Packages

* `sudo apt install --no-install-recommends
  build-essential ca-certificates clang coreutils debhelper dh-python dpkg-dev 
  fakeroot flit gcc git gnome-shell-extension-appindicator make python3 
  python3-all-dev python3-babel python3-build python3-click python3-cpuinfo 
  python3-cryptography python3-dbus python3-dev python3-hkdf python3-ifaddr 
  python3-matplotlib python3-mpmath python3-nacl python3-networkx python3-numpy 
  python3-opencv python3-packaging python3-pathtools python3-pillow python3-pip 
  python3-pluggy python3-progress python3-py python3-pyaudio python3-pydbus 
  python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner 
  python3-pytest-xdist python3-qrcode python3-schema python3-setuptools 
  python3-setuptools-scm python3-pystray python3-sphinx python3-systemd 
  python3-tk python3-toml python3-venv python3-wheel python3-xlib python3-yaml 
  python3-zeroconf sudo time wireguard-tools`

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

Please open an issue to request alternative or additional install documentation.
