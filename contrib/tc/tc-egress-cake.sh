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
FWMARK_TUN_INTERNAL_v4="667";
FWMARK_TUN_INTERNAL_v6="668";
FWMARK_TUN="555";

# tc processing of packets can be bypassed by the kernel unless we are careful.
# If we do not disable this, the kernel may allow hardware to bypass tc
ethtool -K $IFACE_LAN tso off
ethtool -K $IFACE_LAN hw-tc-offload off;

tc qdisc delete root dev $IFACE_LAN || true;
tc filter delete root dev $IFACE_LAN || true;

# We setup our qdisc using cake to do reasonable dynamic traffic shaping
tc qdisc replace dev $IFACE_LAN handle 1: root cake ethernet besteffort egress;

# Allow our tunnel program/kernel module to talk to the local network with
# IPv4 as long as they have the $FWMARK_TUN set in the packet's
# respective skb. This could be a peerwise match with fine grained packet
# checking that matches our expectaitons. If there was a way for a user to set
# an fwmark, they'd be able to bypass and leak, so if they can only leak to a
# peer's tunnel IP and UDP port then it would be a far less useful bypass.
tc filter add dev $IFACE_LAN parent 1: prio 1 protocol ip flower \
  ct_mark $FWMARK_TUN skip_hw action mirred egress redirect dev $IFACE_LAN;

# Allow our tunnel program/kernel module to talk to the local network with
# IPv6 as long as they have the $FWMARK_TUN set in the packet's
# respective skb. This could be a peerwise match with fine grained packet
# checking that matches our expectaitons. If there was a way for a user to set
# an fwmark, they'd be able to bypass and leak, so if they can only leak to a
# peer's tunnel IP and UDP port then it would be a far less useful bypass.
tc filter add dev $IFACE_LAN parent 1: prio 2 protocol ipv6 flower \
  ct_mark $FWMARK_TUN skip_hw action mirred egress redirect dev $IFACE_LAN;

# Rewrite peer IPv6 packets which would otherwise leak out to $IFACE_LAN
tc filter add dev $IFACE_LAN parent 1: prio 3 protocol ipv6 flower \
  src_ip $v6_LL_SELF dst_ip $v6_LL_PEER \
  ct_mark $FWMARK_TUN \
  skip_hw \
  action skbedit mark $FWMARK_TUN_INTERNAL_v6 \
  action mirred egress redirect dev $IFACE_TUN;

# Rewrite peer IPv4 packets which would otherwise leak out to $IFACE_LAN
tc filter add dev $IFACE_LAN parent 1: prio 4 protocol ip flower \
   src_ip $v4_LL_SELF dst_ip $v4_LL_PEER \
   ct_mark $FWMARK_TUN \
   skip_hw \
   action skbedit mark $FWMARK_TUN_INTERNAL_v4 \
   action mirred egress redirect dev $IFACE_TUN;

# Show status
tc qdisc show dev $IFACE_LAN;
tc qdisc show dev $IFACE_TUN;
