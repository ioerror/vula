# Vula Discovery
[Multicast DNS](https://rfc-editor.org/rfc/rfc6762.txt) (mDNS) is currently the protocol that Vula uses to discover peers. This makes Vula dependent on participating devices having mDNS enabled and mDNS traffic not being censored in the network. To reduce that dependency, an alternative option that could be used instead of or along mDNS would be great. Following options were considered:

## LLMNR
[Link-Local Multicast Name Resolution](https://rfc-editor.org/rfc/rfc4795.txt) is a Microsoft-proposed protocol. As the RFC states, the IETF did not achieve consensus on the approach and thus, LLMNR is not an official standard by that mean - nevertheless Microsoft implemented it. 

### Why was it even considered an option for Vula?
LLMNR is very similar to mDNS:
* Same goal - resolving hostnames in the local network without a DNS server
* Same DNS records format (A / AAAA records)
* Also uses multicast (although query responses are unicast)

Therefore, the initial thought was that the implementation could be done quickly and would not require complex changes to the codebase nor to the general principle of Vula discovery. As with mDNS, the Vula descriptor would just be injected in the DNS records.

### Pros
* When mDNS traffic is censored in the network, Vula could use LLMNR to still be able to discover peers.

### Cons
* From a security perspective, it offers little to no benefit. A network censor would need to act naive to block mDNS traffic while letting LLMNR traffic slip through. This is precisely because the protocols are so similar. This situation is less likely than IP multicast just being completely blocked, in which case LLMNR brings no benefit.
* There are no mature libraries available, the analyzed projects have no popularity at all and besides that could not be used directly anyway as for various reasons:
    * [LLamar](https://github.com/joergschulz/llamar) is designed as a standalone service and would require modifications to be 
    * [LocalResolver](https://github.com/mauricelambert/LocalResolver) uses scapy (a too extensive dependency) and is already omitted for that reason.
* Although this argument applies to any alternative, adding one to Vula would add complexity. It would probably be implemented in such a way that the protocol to use is configurable, runs in parallel, or is even dynamically selected based on the network situation. All of this needs coordination, which in turn is an additional source of errors.

### Conclusion
Based on our judgment, the cons outweigh the pros and the necessary work to implement LLMNR is not worth it for the resulting advantages.

## Current recommendation
If you want to invest time to reduce Vulas dependence on mDNS; the best option we think there currently is: Come up with an entirely custom solution/protocol!

Because the search for further similar established protocols, into which we could inject the Vula peer descriptor, turns out to be difficult. Accordingly, there are probably no useful libraries for these protocols that could be implemented quickly.

From what we imagine, that custom solution could be a new protocol on layer 2 that fits Vula-specific needs and is built as resilient to network censorship as possible.

