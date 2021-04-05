#!/bin/bash
set -e

[ "$UID" == "0" ] || (echo this requires sudo; exit 1)

cd "$(dirname "$(readlink -f "$0")")"
source common

for host in $(Hosts); do
    podman run --hostname $host --name $host -v "$(readlink -f ..)":/root/vula --rm --detach --cap-add NET_ADMIN vula /bin/systemd
done

for host in $(Hosts); do
    podman exec -it $host sudo apt install -y python3-systemd policykit-1 less tcpdump avahi-daemon
    podman exec -it $host sudo bash -c 'cd /root/vula; python setup.py install'
    podman exec -it $host vula configure -i eth0
done

for host in $(Hosts); do
    podman exec -it $host vula configure -i eth0
done
