#!/bin/bash
source common
if ExecEach bash -c 'ip route get $(ip route |grep default|cut -f 3 -d " ")'|grep 'dev vula'; then
    echo "It appears the host is routed over vula, so $0 will abort now to avoid losing SSH access to VMs."
    exit 1
fi
set -e
echo "Running stop-drop-caches... "
./stop-drop-caches.sh >/dev/null
echo -n "OK. Confirming there are no peers and no services running..."
if ./inspect.sh|grep -v ^Host|grep -v '0         0      0       0      0           down'; then
    echo
    echo "error: something is not not running. run ./inspect.sh and/or run ./retest.sh again."
    exit 1
else
    echo OK
fi
./restart-services.sh
echo
echo "Now running ./test.sh:"
./test.sh

echo
echo "But wait, there's more... as you are running retest.sh, which took the interface up and down already, we'll do that some more here now:"
echo
echo "Running sync.sh:" # breaks connection if running vula on host...
./test-repair.sh 2>/dev/null
