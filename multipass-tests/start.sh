#!/bin/bash
set -e

cd "$(dirname "$(readlink -f "$0")")"
source common

if [[ "$@" =~ "--rebuild" ]]; then
    rm -rvf ../packer/output-qemu
fi
LaunchAll

echo "Running test.sh"
./test.sh
