#!/bin/bash -x

set -e

sudo apt update

sudo apt install -y --no-install-recommends build-essential debhelper dh-python fakeroot gcc make python3-all python3-all-dev python3-click python3-cpuinfo python3-cryptography python3-dbus python3-dev python3-hkdf python3-ifaddr python3-matplotlib python3-mpmath python3-nacl python3-networkx python3-numpy python3-packaging python3-pathtools python3-pip python3-pluggy python3-progress python3-py python3-pydbus python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner python3-qrcode python3-schema python3-setuptools python3-setuptools-scm python3-stdeb python3-systemd python3-toml python3-yaml python3-zeroconf python3-pyaudio python-all wireguard-tools

sudo pypi-install sibc
sudo pypi-install vula_libnss
sudo pypi-install ggwave
sudo pypi-install vula

echo "vula is now installed"
