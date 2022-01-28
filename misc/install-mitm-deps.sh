#!/bin/bash
set -e

# This script is meant to be run inside of a container.

dist="$(cat /etc/os-release|grep VERSION_CODENAME|cut -f 2 -d=)"

echo "Installing on '$dist'"

attack_deps="tcpdump"
attack_pip_deps="pyfiglet printy scapy pyshark"

apt update
DEBIAN_FRONTEND=noninteractive apt install -y tshark
apt install -y --no-install-recommends --fix-missing $attack_deps
pip3 install $attack_pip_deps

echo "OK: deps installed on $(hostname)"
