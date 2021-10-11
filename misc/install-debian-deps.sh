#!/bin/bash
set -e

# FIXME: some of these packages aren't actually needed anymore

# sibc deps
apt install -y dh-python python3-click python3-progress python3-mpmath python3-numpy python3-matplotlib python3-networkx python3-setuptools-scm python3-setuptools python3-cpuinfo --no-install-recommends
# vula deps
apt install -y wireguard-tools python3-yaml python3-click python3-nacl python3-schema python3-pip python3-pathtools make gcc python3-pydbus python3-click-man python3-pyroute2 python3-pytest-runner click-man python-is-python3 python3-pytest python3-toml python3-py python3-packaging python3-pluggy python3-hkdf python3-ifaddr python3-cryptography python3-dbus python3-pygments python3-systemd python3-qrcode python3-all python-all fakeroot build-essential dh-python debhelper python3-dev --no-install-recommends

# even if also installed with pip, we install these here to satisfy the debian dependency for zeroconf
apt install -y python3-zeroconf python3-stdeb --no-install-recommends

# on ubuntu 20.10 and earlier, to get newer versions that fix some bugs:
# sudo pip3 install -U zeroconf
# sudo pip3 install stdeb

pip3 install sibc
pip3 install vula_libnss

# for latest version:
#sudo pip3 install git+https://github.com/JJChiDguez/sibc

echo "OK: deps installed on $(hostname)"
