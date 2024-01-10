#!/bin/bash
set -e

# pypi-install highctidh
# for latest version:
# pip3 install git+https://codeberg.org/vula/highctidh/
apt install -y --no-install-recommends flit
git clone https://codeberg.org/vula/highctidh/
cd highctidh;
git checkout v1.0.2024010701
VERSION=`cat VERSION`;
time make -f Makefile.packages deb
ls -al *
ls -al dist/
dpkg -i `pwd`/dist/python3-highctidh*.deb

echo "OK: highctidh installed on $(hostname)"
