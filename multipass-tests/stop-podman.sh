#!/bin/bash
set -e

[ "$UID" == "0" ] || (echo this requires sudo; exit 1)

source common

for host in $(Hosts); do
    podman stop $host 
done

