#!/bin/bash

set -e;
export DEBIAN_FRONTEND=noninteractive

apt update;
apt install -y --no-install-recommends \
  build-essential ca-certificates clang coreutils debhelper dh-python dpkg-dev \
  fakeroot flit gcc git gnome-shell-extension-appindicator make python3 \
  python3-all-dev python3-babel python3-build python3-click python3-cpuinfo \
  python3-cryptography python3-dbus python3-dev python3-ifaddr \
  python3-matplotlib python3-mpmath python3-nacl python3-networkx python3-numpy \
  python3-opencv python3-packaging python3-pathtools python3-pillow python3-pip \
  python3-pluggy python3-progress python3-py python3-pyaudio python3-pydbus \
  python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner \
  python3-pytest-xdist python3-qrcode python3-schema python3-setuptools \
  python3-setuptools-scm python3-pystray python3-sphinx python3-systemd \
  python3-tk python3-toml python3-venv python3-wheel python3-xlib python3-yaml \
  python3-zeroconf sudo time wireguard-tools;

# pymonocypher
apt install -y --no-install-recommends \
  cython3 build-essential python3 python3-venv python3-build debhelper-compat \
  pybuild-plugin-pyproject python3-all-dev python3-numpy python-is-python3;

# reunion
apt install -y --no-install-recommends \
  build-essential python3 python3-venv flit dh-python debhelper git \
  pybuild-plugin-pyproject python3-setuptools python3-hkdf python3-flask \
  python3-stem python3-socks;

# ggwave
#apt install -y --no-install-recommends \
#  cython3 build-essential cmake debhelper-compat dh-python python3-all-dev \
#  python3-build python3-cogapp python3-venv;

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
#if [ ! -d ggwave ];
#then
#  git clone --recursive https://www.github.com/ggerganov/ggwave
#else
#  cd ggwave && git pull && cd ..;
#fi
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
export CC=gcc;
cd vula_libnss && make clean && make deb; cd ..;
cd pymonocypher && make clean && make deb; cd ..;
#cd ggwave && cmake . -DGGWAVE_BUILD_EXAMPLES=OFF -DCMAKE_BUILD_TYPE=Release \
#          && make deb; cd ..;
cd reunion && make clean && make deb; cd ..;
export CC=clang;
cd highctidh && make clean && make deb; cd ..;
echo "Hashes for the Debian packages:";
sha256sum */dist/*.deb;
#319c83905dedfe4b12e044acd205529d021952e51c0eae8dec13c34839f18bf1  highctidh/dist/python3-highctidh_1.0.2024092800-1_amd64.deb
#80749d8c526ff8e954a9e733a29b2b18369280da1898fcfc7a0f7fc8a8230a61  pymonocypher/dist/python3-pymonocypher-dbgsym_4.0.2.5-0_amd64.deb
#fbd00fd0b815ffc1743394613625753a769772b5f4e7bd302bf242a69530a3e6  pymonocypher/dist/python3-pymonocypher_4.0.2.5-0_amd64.deb
#29e60950153532744cfe4beccf96a0d6176186a292c1baa93252980fac01ccc4  reunion/dist/python3-rendez_1.2.1-1_all.deb
#5315cd2269b4aa2e1ae7b4da832afcb124d0a0a294448c9d4ce5bd684af02b02  vula_libnss/dist/python3-vula-libnss-dbgsym_0.0.2024120900-1_amd64.deb
#a22536cc47e3cbfb4cb55159bf6616ba5724b446d9534c7ffba806e2e0535199  vula_libnss/dist/python3-vula-libnss_0.0.2024120900-1_amd64.deb

