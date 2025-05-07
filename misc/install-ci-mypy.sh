#!/bin/bash -x

apt update -y

# plucky podman container setup:
DEBIAN_FRONTEND=noninteractive apt install -y libgcc-s1 libstdc++6 python3 python3-click \
python3-cryptography python3-nacl python3-pillow \
python3-pyaudio python3-pydbus python3-pyroute2 python3-pystray \
python3-qrcode python3-schema python3-tk python3-yaml \
python3-zeroconf python3-pip sudo

DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
build-essential ca-certificates clang coreutils debhelper dh-python dpkg-dev \
fakeroot flit gcc git gnome-shell-extension-appindicator make python3 \
python3-all-dev python3-babel python3-build python3-click python3-cpuinfo \
python3-cryptography python3-dbus python3-dev python3-ifaddr \
python3-matplotlib python3-mpmath python3-nacl python3-networkx python3-numpy \
python3-opencv python3-packaging python3-pathtools python3-pillow python3-pip \
python3-pluggy python3-progress python3-py python3-pyaudio python3-pydbus \
python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner \
python3-pytest-xdist python3-qrcode python3-schema python3-setuptools \
python3-setuptools-scm python3-pystray python3-socks python3-sphinx python3-systemd \
python3-tk python3-toml python3-venv python3-wheel python3-xlib python3-yaml \
python3-zeroconf time wireguard-tools;

# pymonocypher
DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
cython3 build-essential python3 python3-venv python3-build debhelper-compat \
pybuild-plugin-pyproject python3-all-dev python3-numpy python-is-python3;

# reunion
DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
build-essential python3 python3-venv flit dh-python debhelper git \
pybuild-plugin-pyproject python3-setuptools python3-flask \
python3-stem;

# ggwave
DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
cython3 build-essential cmake debhelper-compat dh-python python3-all-dev \
python3-build python3-cogapp python3-venv;

apt install -y mypy
pip install --break-system-packages pyroute2 zeroconf schema cryptography click pydbus highctidh pyyaml pynacl qrcode pillow rendez setuptools pyaudio pystray babel black isort flake8 mypy packaging pylint pytest pytest-cov pygobject-stubs pydeps pyfiglet printy build pygobject pydbus-stubs opencv-python