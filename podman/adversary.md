# PoC Passive and Active Adversary

## Usage

Prerequisites: Podman installed, read the README.md in the podman folder.

* use "make test-passive-adversary" to create PCAP in network with two peers
* use "make test-active-adversary" to start our attacker script. (Currently only poisoning MDNS cache)
* use "make clean-all" to delete everything
* use "make mallory-stop" to stop Mallory
* use "make mallory-clean" remove mallory machine and image

## Pitfalls

* does not record mDNS stuff everytime -> caching?
  * Solution: make clean && make test-mitm (containers in improper state and ping not executed.
* make ARP cache poisoning to MitM the ping
  1. do arp cache poisoning
  2. create loop to send every 5s a ping
  * Does not work, no ARP in podman networks

## ToDo's

* Issue: When running test-mitm again, it builds the image again and wants to create the container which fails
  * Workaround: Suppressed error msg
* clean up naming and stuff (mallory, mitm, attacker, container, images, stamps and everything..)
