#!/bin/bash
suffix="$1"
source common
if [ "$suffix" = "" ]; then suffix=".local."; fi
(
    echo -ne "from\t to \t"
    for n in $(seq $INSTANCE_COUNT); do
        echo -ne "$n\t"
    done
    echo
    for host in $(Hosts); do
        echo -e "${host}${suffix}\t -\t$(
            Exec $host bash -c '
                for host in '"$(echo $(Hosts))"'; do
                    ping -c 1 $host'$suffix' > /dev/null 2>/dev/null &&
                    echo -ne "ok\t" ||
                    echo -ne "fail\t"
                done')" &
    done
    wait
) | sort | column -t
