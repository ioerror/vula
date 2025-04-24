#!/bin/bash
# This is an example where we only have one lan interface with one link-local
# address. It is trivial to extend this to many where there is a one to one
# correspondance of link-local pairs.
# It is also possible to use tc to enforce policy on packets with our synthetic
# address.
# Other projects could easily adapt this strategy to enforce policy.
# tc processes packets after the POSTROUTING (netfilter) stage.

set -ex;

v6_LL_PEER="fe80::1638:df38:d7b9:540b";
v6_LL_SELF="fe80::61b6:3d84:6035:3227";
IFACE_LAN="wlp82s0";
IFACE_TUN="vula";
FWMARK_TUN_INTERNAL="667";

tc qdisc del dev $IFACE_TUN root || true;
tc qdisc del dev $IFACE_TUN clsact || true;

# Install clsact (no shaping, just provides ingress+egress filter hooks)
tc qdisc replace dev $IFACE_TUN clsact;

# Rewrite peer IPv6 packets which would otherwise be silently dropped
tc filter add dev $IFACE_TUN ingress prio 1 protocol ipv6 flower \
    src_ip   $v6_LL_PEER     \
    dst_ip   $v6_LL_SELF     \
    skip_hw                 \
    action   skbedit mark $FWMARK_TUN_INTERNAL \
    action   mirred ingress redirect dev $IFACE_LAN;

# Show status
tc qdisc show dev $IFACE_LAN;
tc qdisc show dev $IFACE_TUN;
