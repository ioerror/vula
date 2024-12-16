#!/bin/bash
set -e
apt install -y --no-install-recommends flit
git clone https://codeberg.org/vula/highctidh/
cd highctidh;
git checkout v1.0.2024092800
make deb
ls -al *
ls -al dist/
dpkg -i `pwd`/dist/python3-highctidh*.deb
echo "OK: highctidh installed on $(hostname)"
