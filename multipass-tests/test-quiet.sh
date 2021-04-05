#!/bin/bash

#FIXME: we could write some actual tests here. currently, this script relies on
# a human being to read its output to see that things are working.

echo -n "Ping multipass names: "
./ping.sh .multipass >/dev/null || echo FAIL && echo PASS
echo -n "Ping .local. names: "
./ping.sh .local. >/dev/null || echo FAIL && echo PASS

./test-repair.sh 2>/dev/null
