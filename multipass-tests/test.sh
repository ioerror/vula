#!/bin/bash

source common

Exec $(Hosts|head -1) bash -c 'cd vula && PY_IGNORE_IMPORTMISMATCH=1 python3 setup.py test'

set -e

echo
echo "At this point, each host should have two peers, but won't have done a handshake with any yet:"
./inspect.sh
echo
echo "Now we'll run our first ping, which can take a few seconds for some reason (possibly multipass-related? wireguard shouldn't take this long...):"
./ping.sh .local.

echo
echo "Now, if all went well, we should see that each peer has completed a handshake and sent and received data:"
./inspect.sh

echo
echo -n "Confirming each host has expected number of entries in its NSS hosts database... "
ExecEach -e bash -c '[ $(getent hosts|wc -l) -ge $(($INSTANCE_COUNT + 2)) ]' >/dev/null
echo OK

echo
echo "Now we'll do one more round of pings (which should be much faster):"
./ping.sh .local.

echo -n "Confirming each host has expected number of transfer lines in wg output... "
ExecEach -e sudo bash -c '[ $(wg|grep transfer|wc -l) -ge $(( $INSTANCE_COUNT - 1 )) ]' >/dev/null
echo OK
echo
echo "This concludes our test program."
echo "You'll have to read the above output carefully to see if things are actually working."
echo "You can also now run ./retest.sh to drop caches and routes and restart services and test again."
echo
echo "Don't forget to run ./stop.sh to delete the VMs when you're done."

