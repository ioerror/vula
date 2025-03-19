#!/bin/bash
set -e

# This script is meant to be run inside of a container.
#
# See quick-install.sh for the script meant to be run on real systems.
#
# This script is recently only tested and working with bookworm.

dist="$(cat /etc/os-release|grep VERSION_CODENAME|cut -f 2 -d=)"

echo "Installing on '$dist'"

ci_deps="pkg-config libglib2.0-dev libcairo2-dev libgirepository1.0-dev libgirepository-2.0-dev python3-all-dev python3-tk make git portaudio19-dev gcc clang python3 python3-build python3-setuptools build-essential python3-venv python3-wheel python3-pip dh-python flit debhelper dh-python fakeroot python3-setuptools rpm python3-xlib xvfb xauth python3-pytest"

apt update
apt install -y --no-install-recommends $ci_deps

python -m pip install --user pipx
python -m pipx ensurepath
pipx install pipenv
pipenv install -v async_timeout
pipenv install -v highctidh
pipenv install -v --dev --skip-lock

echo "OK: deps installed on $(hostname)"
