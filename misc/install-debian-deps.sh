#!/bin/bash
set -e

# This script is meant to be run inside of a container.
#
# See quick-build.sh for a build procedure meant to be run on real systems.
#
# This script is recently only tested and working with bookworm.

dist="$(cat /etc/os-release|grep VERSION_CODENAME|cut -f 2 -d=)"

echo "Installing on '$dist'"

vula_deps="wireguard-tools python3-yaml python3-click python3-nacl python3-schema python3-pip python3-pathtools make gcc python3-pydbus python3-pyroute2 python3-pytest-runner python3-pytest python3-toml python3-py python3-packaging python3-pluggy python3-hkdf python3-ifaddr python3-cryptography python3-dbus python3-pygments python3-systemd python3-qrcode python3-all fakeroot build-essential dh-python debhelper python3-dev python3-zeroconf python3-all-dev python3-build python3-babel python3-tk python3-sphinx python3-xlib python3-pillow gir1.2-ayatanaappindicator3-0.1 python3-pyaudio python3-venv python3-click-man click-man"

podman_deps="containernetworking-plugins"

apt update
apt install -y --no-install-recommends $vula_deps $podman_deps

#pypi-install ggwave
# pip3 install ggwave

# install vula_libnss
git clone --recursive https://codeberg.org/vula/vula_libnss
cd vula_libnss && make deb && dpkg -i dist/*.deb

# python3-pystray is only available in Debian Unstable so far
#DEB_BUILD_OPTIONS=nocheck pypi-install pystray

echo "OK: deps installed on $(hostname)"
