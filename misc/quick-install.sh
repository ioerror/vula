#!/bin/bash

set -e;

sudo apt update;
sudo DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
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

# pymonocypher
sudo DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
  cython3 build-essential python3 python3-venv python3-build debhelper-compat \
  pybuild-plugin-pyproject python3-all-dev python3-numpy python-is-python3;

# reunion
sudo DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
  build-essential python3 python3-venv flit dh-python debhelper git \
  pybuild-plugin-pyproject python3-setuptools python3-hkdf python3-flask \
  python3-stem;

# ggwave
sudo DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
  cython3 build-essential cmake debhelper-compat dh-python python3-all-dev \
  python3-build python3-cogapp python3-venv;

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
if [ ! -d ggwave ];
then
  git clone --recursive https://www.github.com/ggerganov/ggwave
else
  cd ggwave && git pull && cd ..;
fi
if [ ! -d pymonocypher ];
then
  git clone --recursive https://github.com/jetperch/pymonocypher/
else
  cd pymonocypher && git pull && cd ..;
fi
if [ ! -d reunion ];
then
  git clone --recursive https://www.codeberg.org/rendezvous/reunion
else
  cd reunion && git pull && cd ..;
fi
mkdir -p dist
make clean && make deb
export CC=gcc;
cd vula_libnss && make clean && make deb; cd ..;
cd pymonocypher && make clean && make deb; cd ..;
cd ggwave && cmake . -DGGWAVE_BUILD_EXAMPLES=OFF -DCMAKE_BUILD_TYPE=Release \
          && make deb; cd ..;
cd reunion && make clean && make deb; cd ..;
export CC=clang;
cd highctidh && make clean && make deb; cd ..;
echo "Hashes for the Debian packages:";
sha256sum dist/*.deb;
sha256sum vula_libnss/dist/*.deb;
sha256sum highctidh/dist/*.deb;
sha256sum ggwave/dist/*.deb;
sha256sum pymonocypher/dist/*.deb;
sha256sum reunion/dist/*.deb;
echo "Install the following Debian packages:";
ls -1 dist/*.deb;
ls -1 vula_libnss/dist/*.deb;
ls -1 highctidh/dist/*.deb;
ls -1 ggwave/dist/*.deb;
ls -1 pymonocypher/dist/*.deb;
ls -1 reunion/dist/*.deb;
