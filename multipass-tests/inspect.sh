#!/bin/bash

set -e
source common

( echo -e "Host\t Services\t Names\t Routes\t Peers\t Handshakes\t iface\t IP"
  for host in $(Hosts); do
    Exec $host sudo bash -c '
        set -e
        services="$(systemctl status|grep bin/vula|grep -v grep|wc -l)"
        routes="$(ip route show table 666|wc -l)"
        peers="$(wg|grep ^peer|wc -l)"
        names="$(cat /var/lib/vula-organize/hosts |wc -l)"
        handshakes="$(wg|grep handshake|wc -l)"
        wg="$(wg|grep vula >/dev/null && echo "up" || echo "down")"
        ip="$(ip a|grep "inet "|grep -v 127.0.0.1|awk "{print \$2}"|xargs echo)"
        echo -e "'$host'\t $services\t $names\t $routes\t $peers\t $handshakes\t $wg\t $ip"         ' &
  done
  wait
) | sort | column -t

