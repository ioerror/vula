# Vula Man-in-the-Middle Testing
The Vula Man-in-the-Middle Testing consists of an active and a passive adversary tests.
These tests should on one side support the developers to test, if the theoretical threat model applies in practice.
It further enables everybody to verify their security (or insecurity ;-) )

## Project State
Our goal was to provide an Man-in-the-Middle tool for _unverified_ & _unpinned_ peers and to automate this in a podman test.

### Passive Adversary Test
The passive adversary tests simulates a listening adversary sitting inbetween two vula peers.
This test was not intended in the purposal, but made additionally since it is a useful test.
A developer can see with this tests, whether two vula peers communicate encrypted with each other.
While a passive adversary does only listen, our test uses ARP spoofing (an active attack) to simulate the passive adversary.
The passive adversary captures multiple pings between the vula peers.
The captured traffic is then analyzed, if the pings are encrypted the test passes, if the pings are sent unencrypted the test fails.

### Active Adversary Test
The active adversary tests if a _unverified_ and _unpinned_ Vula peer can be poisoned with a malicious Vula mDNS record.
The test does not intercept nor forward traffic, the test listens for Vula mDNS requests and creates malicious mDNS records to poison the targeted vula peers.
After sending the malicious mDNS request, the test checks whether the vula peers cache contains the malicious mDNS record by checking if the IP address matches with the attackers IP.

### Usage

Go into the podman directory
```cd podman```

To run the passive adversary test:
```make passive-adversary-test```

To run the active adversary test:
```make active-adversary-test```

Clean everything up
```make clean-sudo```



### Code

* podman/Makefile -> contains the tests and check functions
* test-passive-adversary.py -> script contains functionality for passive adversary and some utility functions
* forge_descriptor.py -> Library to create forged descriptors
* mdns_poison.py -> script contains functionality for active adversary (mDNS poisoning)

### Future Work
* The active adversary's skript currently poisons a vula peer's cache. The script could easily be enhanced to spin up corresponding wireguard interfaces to intercept traffic between poisoned peers. For this to work, the package forwarding needs to be implemented too.
* The reliability of the tests could be improved.
* Make a test to show how much traffic is encrypted when somebody uses vula.
  * use test-passive-adversary as template
  * the targeted vula peers could do some communication (eg. http)
  * the passive adversary can capture the traffic, analyze the traffic and create statistics

### Comments and known bugs
* Our tests need CAP_NET_RAW and therefore rootfull containers are needed.
* Both tests are somewhat unstable, if the test fails, run again (2-3 times)
  * Reason: Automate network attacks is tricky, since we depend on the answers of the targets
* test-passive-adversary fails sometimes due to name resolution in podman networks fail. Try make clean-sudo in these cases.
Additionally clean the network sudo podman network rm vula-net
* make clean and make clean-all does not clean rootfull containers/images etc. make clean-sudo is needed