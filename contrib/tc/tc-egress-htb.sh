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

tc qdisc del dev $IFACE_LAN root || true;
tc filter del dev $IFACE_LAN root || true;

# We setup our HTB with two classes (one for the tunnel program/kernel module
# to bypass, one does redirection)
tc qdisc add dev $IFACE_LAN root handle 1: htb default 10;
tc class add dev $IFACE_LAN parent 1: classid 1:10 htb rate 1000mbit ceil 1000mbit;
tc class add dev $IFACE_LAN parent 1: classid 1:20 htb rate 1000mbit ceil 1000mbit;

# Allow our tunnel program/kernel module to talk to the local network with
# either IPv4 or IPv6 as long as they have the $FWMARK_TUN set in the packet's
# respective skb
tc filter add dev $IFACE_LAN parent 1: prio 1 handle $FWMARK_TUN/0xffffffff \
  fw classid 1:10;

# Rewrite peer IPv6 packets which would otherwise leak out to $IFACE_LAN
tc filter add dev $IFACE_LAN parent 1: prio 2 protocol ipv6 flower \
  src_ip $v6_LL_SELF dst_ip $v6_LL_PEER flowid 1:20 \
  action skbedit mark $FWMARK_TUN_INTERNAL \
  action mirred egress redirect dev $IFACE_TUN;

# Rewrite peer IPv4 packets which would otherwise leak out to $IFACE_LAN
tc filter add dev $IFACE_LAN parent 1: prio 3 protocol ip flower \
   src_ip $v4_LL_SELF dst_ip $v4_LL_PEER flowid 1:20 \
   action skbedit mark $FWMARK_TUN_INTERNAL \
   action mirred egress redirect dev $IFACE_TUN;

# Show status
tc qdisc show dev $IFACE_LAN;
tc qdisc show dev $IFACE_TUN;
