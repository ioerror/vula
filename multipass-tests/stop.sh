#!/bin/bash
source common
for host in $(Hosts); do
    echo "stopping instance $host"
    multipass delete --purge $host
    sleep 2 # multipass seems to not like having instances deleted too fast
            # otherwise multipassd dies and says:
            #       double free or corruption (fasttop)
done
echo OK: deleted test instances
