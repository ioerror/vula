#!/bin/bash -x

apt update -y;

# plucky podman container setup:
DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
    build-essential ca-certificates clang cmake coreutils cython3 \
    debhelper debhelper-compat dh-python dpkg-dev fakeroot flit gcc git \
    gnome-shell-extension-appindicator make mypy pybuild-plugin-pyproject \
    python-is-python3 python3 python3-all-dev python3-babel python3-build \
    python3-click python3-cogapp python3-cryptography python3-cpuinfo \
    python3-dbus python3-dev python3-flask python3-ifaddr python3-matplotlib \
    python3-mpmath python3-nacl python3-networkx python3-numpy \
    python3-opencv python3-packaging python3-pathtools python3-pillow \
    python3-pip python3-pluggy python3-progress python3-pyaudio \
    python3-pydbus python3-pygments python3-pyroute2 python3-pystray \
    python3-pytest python3-pytest-runner python3-pytest-xdist \
    python3-qrcode python3-schema python3-setuptools \
    python3-setuptools-scm python3-socks python3-sphinx python3-stem \
    python3-systemd python3-tk python3-toml python3-venv python3-wheel \
    python3-xlib python3-yaml python3-zeroconf sudo time wireguard-tools;

pip install --break-system-packages \
    babel black build click cryptography flake8 highctidh isort \
    mypy opencv-python packaging pillow printy pyaudio pydbus pydbus-stubs \
    pydeps pygobject pygobject-stubs pyfiglet pluggy progress pyroute2 \
    pyaudio pynacl pystray pytest pytest-cov qrcode rendez schema setuptools \
    zeroconf pyyaml;
