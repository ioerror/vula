#!/bin/bash
set -e
source common
ExecEach -e sudo apt install -y avahi-autoipd
ExecEach -e sudo bash -c 'avahi-autoipd -c '${INTERFACE}' || avahi-autoipd --daemonize --wait --force-bind '${INTERFACE}
./restart-services.sh
./inspect.sh
ExecEach -e vula peer
echo
echo "You can run this:"
echo "  ExecEach sudo killall avahi-autoipd"
echo "  ./retest.sh"
echo
echo "to return the test instances to the single-IP state."
