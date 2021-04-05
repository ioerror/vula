#!/bin/bash
source common
set -ex
ExecEach -e bash -lc vula-install
ExecEach -e sudo systemctl enable vula-organize
./restart-services.sh #FIXME: race makes this necessary
echo "OK: reinstalled; you can run ./test.sh now"
