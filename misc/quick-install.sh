#!/bin/bash

set -e;

sudo apt update;
sudo apt install -y --no-install-recommends \
  build-essential ca-certificates clang coreutils debhelper dh-python dpkg-dev \
  fakeroot flit gcc git gnome-shell-extension-appindicator make python3 \
  python3-all-dev python3-babel python3-build python3-click python3-cpuinfo \
  python3-cryptography python3-dbus python3-dev python3-hkdf python3-ifaddr \
  python3-matplotlib python3-mpmath python3-nacl python3-networkx python3-numpy \
  python3-opencv python3-packaging python3-pathtools python3-pillow python3-pip \
  python3-pluggy python3-progress python3-py python3-pyaudio python3-pydbus \
  python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner \
  python3-pytest-xdist python3-qrcode python3-schema python3-setuptools \
  python3-setuptools-scm python3-pystray python3-sphinx python3-systemd \
  python3-tk python3-toml python3-venv python3-wheel python3-xlib python3-yaml \
  python3-zeroconf sudo time wireguard-tools;

if [ ! -d highctidh ];
then
  git clone https://www.codeberg.org/vula/highctidh;
else
  cd highctidh && git pull && cd ..;
fi
if [ ! -d vula_libnss ];
then
  git clone --recursive https://www.codeberg.org/vula/vula_libnss
else
  cd vula_libnss && git pull && cd ..;
fi
make clean && make deb
export CC=gcc;
cd vula_libnss && make clean && make deb; cd ..;
export CC=clang;
cd highctidh && make clean && make deb; cd ..;
echo "Install the following Debian packages:";
ls highctidh/dist/*.deb;
ls vula_libnss/dist/*.deb;
ls dist/*.deb;
