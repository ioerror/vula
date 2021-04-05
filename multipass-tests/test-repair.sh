#!/bin/bash
set -e
source common
echo -n "Testing to confirm repair has no work to do:            "
#ExecEach sudo vula repair|grep -vE -- "---" && echo FAIL || echo PASS
lines=$(ExecEach sudo vula repair -n|wc -l)
if [ "$lines" -eq $INSTANCE_COUNT ]; then echo PASS; else echo FAIL; fi

echo "Deleting device to give repair something to do"
ExecEach bash -c 'sudo ip link delete vula'

# each instance has 1 line for its name, 6 lines for creating, bringing up, and
# configuring the device, plus 3 lines for each of its N-1 peers
target=$(( $INSTANCE_COUNT * (1 + 6 + 3 * ($INSTANCE_COUNT - 1)) ))

echo -n "Testing if repair --dry-run has $target lines:               "
lines=$(ExecEach sudo vula repair --dry-run|wc -l)
if [ "$lines" -eq $target ]; then echo PASS; else echo "FAIL ($lines)"; fi

echo -n "Testing if repair has $target lines:                         "
lines=$(ExecEach sudo vula repair|wc -l)
if [ "$lines" -eq $target ]; then echo PASS; else echo "FAIL ($lines)"; fi

echo -n "Testing if second repair has no output:                 "
ExecEach sudo vula repair|grep -vE -- "---" && echo FAIL || echo PASS
#lines=$(ExecEach sudo vula repair|wc -l)
#if [ "$lines" -eq 3 ]; then echo PASS; else echo FAIL; fi
