#!/bin/bash
#
# This is an example where we only have one lan interface with one link-local
# address. It is trivial to extend this to many where there is a one to one
# correspondance of link-local pairs.
# It is also possible to use tc to enforce policy on packets with our synthetic
# address.
# Other projects could easily adapt this strategy to enforce policy.
# tc processes packets after the POSTROUTING (netfilter) stage

set -ex;

v6_LL_PEER="fe80::1638:df38:d7b9:540b";
v6_LL_SELF="fe80::61b6:3d84:6035:3227";
v6_SYN_SELF="fd::1";
v6_SYN_PEER="fd::2";
v4_LL_SELF="192.168.2.24";
v4_LL_PEER="192.168.2.220";
IFACE_LAN="wlp82s0";
IFACE_TUN="vula";
FWMARK_TUN_INTERNAL="667";
FWMARK_TUN="555";

# tc processing of packets can be bypassed by the kernel unless we are careful.
# If we do not disable this, the kernel may allow hardware to bypass tc
ethtool -K $IFACE_LAN tso off;
ethtool -K $IFACE_LAN hw-tc-offload off;

# remove any old clsact, then install it
tc qdisc del dev $IFACE_LAN root 2>/dev/null || true;
tc qdisc del dev $IFACE_LAN egress 2>/dev/null || true;
tc qdisc del dev $IFACE_LAN ingress 2>/dev/null || true;
tc qdisc del dev $IFACE_LAN clsact 2>/dev/null || true;
tc qdisc add dev $IFACE_LAN clsact || true;
tc qdisc replace dev $IFACE_LAN clsact;

# IPv4 bypass: packets already marked with FWMARK_TUN are redirected back out
tc filter add dev $IFACE_LAN egress prio 1 protocol ip flower \
    ct_mark $FWMARK_TUN skip_hw \
    action mirred egress redirect dev $IFACE_LAN;

# IPv6 bypass: packets already marked with FWMARK_TUN are redirected back out
tc filter add dev $IFACE_LAN egress prio 2 protocol ipv6 flower \
    ct_mark $FWMARK_TUN skip_hw \
    action mirred egress redirect dev $IFACE_LAN;

# IPv4 rewrite: from v4 link-local SELF to PEER, mark and redirect to tunnel
tc filter add dev $IFACE_LAN egress prio 3 protocol ip flower \
    src_ip $v4_LL_SELF dst_ip $v4_LL_PEER skip_hw \
    action skbedit mark $FWMARK_TUN_INTERNAL \
    action mirred egress redirect dev $IFACE_TUN;

# IPv6 rewrite: from v6 link-local SELF to PEER, mark and redirect to tunnel
tc filter add dev $IFACE_LAN egress prio 4 protocol ipv6 flower \
    src_ip $v6_LL_SELF dst_ip $v6_LL_PEER skip_hw \
    action skbedit mark $FWMARK_TUN_INTERNAL \
    action mirred egress redirect dev $IFACE_TUN;

# Show status
tc qdisc show dev $IFACE_LAN;
tc qdisc show dev $IFACE_TUN;
