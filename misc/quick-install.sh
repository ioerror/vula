#!/bin/bash -x

set -e

sudo apt update

# sibc dependencies
sudo apt install --no-install-recommends -y dh-python python3-click \
  python3-progress python3-numpy python3-matplotlib python3-networkx \
  python3-stdeb python3-setuptools-scm python3-setuptools python3-cpuinfo \
  python3-all-dev

# vula dependencies
sudo apt install --no-install-recommends -y wireguard wireguard-tools \
python3-yaml python3-click python3-nacl python3-schema python3-pip \
python3-pydbus python3-pyroute2 python3-pytest-runner python3-pytest \
python3-toml python3-py python3-packaging python3-pluggy python3-hkdf \
python3-ifaddr python3-cryptography python3-dbus python3-pygments \
python3-systemd python3-qrcode python3-all python-all fakeroot build-essential \
dh-python debhelper make gcc python3-all-dev python3-zeroconf

# stdeb dependencies
sudo apt install --no-install-recommends -y apt-file libapt-pkg-perl \
libexporter-tiny-perl liblist-moreutils-perl libregexp-assemble-perl

# unpackaged or only dependencies, we install three packages as Debian packages
sudo pypi-install --keep stdeb
sleep 1
sudo pypi-install --keep zeroconf
sleep 1
sudo pypi-install --keep sibc
sleep 1

# Download the source for vula_libnss and vula
tmp_dir=$(mktemp -d -t vula-XXX-XXX)
mkdir $tmp_dir
cd $tmp_dir
git clone --recurse-submodules https://codeberg.org/vula/vula_libnss
git clone https://codeberg.org/vula/vula

# build the packages
cd vula_libnss && make deb
cd ..
cd vula && make deb
cd ..

# install the packages we have just built:
sudo dpkg -i vula_libnss/deb_dist/python3-vula-libnss_*.deb
sudo dpkg -i vula/deb_dist/python3-vula_*_all.deb
