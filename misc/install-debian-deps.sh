#!/bin/bash
set -e

# FIXME: some of these probably aren't needed anymore

sibc_deps="dh-python python3-click python3-progress python3-mpmath python3-numpy python3-matplotlib python3-networkx python3-setuptools-scm python3-setuptools python3-cpuinfo python3-all build-essential fakeroot"

vula_deps="wireguard-tools python3-yaml python3-click python3-nacl python3-schema python3-pip python3-pathtools make gcc python3-pydbus python3-click-man python3-pyroute2 python3-pytest-runner click-man python-is-python3 python3-pytest python3-toml python3-py python3-packaging python3-pluggy python3-hkdf python3-ifaddr python3-cryptography python3-dbus python3-pygments python3-systemd python3-qrcode python3-all python-all fakeroot build-essential dh-python debhelper python3-dev python3-zeroconf python3-stdeb python3-all-dev"

apt install -y --no-install-recommends $sibc_deps $vula_deps

pypi-install sibc
# for latest version:
# pip3 install git+https://github.com/JJChiDguez/sibc

pypi-install vula_libnss
# for latest version:
# git clone --recursive https://codeberg.org/vula/vula_libnss
# cd vula_libnss && make deb && dpkg -i deb_dist/*.deb

# on older distributions it may be necessary to get newer versions of some
# packages from pypi:
# sudo pypi-install -U zeroconf
# sudo pypi-install stdeb

echo "OK: deps installed on $(hostname)"
