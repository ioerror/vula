# Abstract
We did an IPv6 compatibility analysis for the Vula project in which we sought to answer whether Vula in its current state is IPv6-compatible.
If Vula turns out not to be compatible yet, we would perform a code analysis to determine which parts of Vula are not yet compatible.
This report documents our work and documents the current incompatibilities, both in the Vula codebase as well as external libraries to consider.

# Preliminaries
## Introduction
> IPv6 is important. Vitally important, in fact. Downright critical.

_Criekct Liu_\
_Tom Coffeen_

In recent years, computer science has been dealing with a central problem: the scarcity of IPv4 addresses. When IPv4 was developed in the 1980s, there were enough addresses to give everyone in the world an address. But the world has changed since then. In 2015, the American Registry for Internet Numbers (ARIN), responsible for assigning IP addresses to companies in North America, officially ran out of addresses. Although technologies such as NAT have postponed the inevitable somewhat, IPv6, as drafted in December 1998, was ratified as an internet standard in July 2017.

As IPv6 is not just an extension to IPv4, it only works if the networking infrastructure, including applications operating on a network level such as VPN or network security software, is compatible to IPv6. Therefore, the authors of this paper consider it absolutely paramount to either make software IPv6 compatible or provide compatible alternatives.

In addition to upgrading the Internet from IPv4 to IPv6, the community is concerned about one danger: surveillance. Personal networks are often operated without comprehensive protection against surveillance attacks. The software Vula, which is currently under development, counteracts this. With features such as automated peer-to-peer encryption and a non-unicast communication, the software ensures that communication is protected. It is currently unclear whether and to what level Vula is IPv6 compatible. The software has been tested and used primarily in IPv4 environments. 

This paper investigates whether Vula is already IPv6 compatible and which components prevent compatibility with IPv6. For this purpose, static code analysis and automated tests were used. This report collects the findings and documents the current status of compatibility. Thanks to the automated tests, the findings are also integrated into the code to facilitate future work efforts.

## Scope and Delimitation
The aim of this work is to show where the code needs to be adapted in order to achieve full IPv6 compatibility. Statements on how the changes must be implemented are not part of the work. Determining the IPv6 compatiblitiy of external libraries was done through the available documentation, as the codebase of external libraries is out of scope by design. 

Vula is usually used in private networks whose segments are defined by RFC 1918. 

As IPv6 lacks such private network segments, the analysis was done under the assumption that IPv6-specific link-local addresses as defined in RFC 4291 will be used.
Since neither routing nor NAT are included in the scope of Vula and the discovery works via multicast, this offers the required functionalities without introducing potential leaking of information outside of the network. 

## Project
### Proceedings

At the beginning, we individually expanded our knowledge on the topic of IPv6 and discussed which approach is best suited to answer this question.

Later, we created a fork of the Vula repository so that all subsequent work would be done on the same basis.
This ensured that there were no modifications that could affect the analysis process (line shifts in the code, etc.).

We then split the source code per person and used it to perform a manual code analysis.
In this, we focused our attention on whether there were any parts, which are not compatible and which dependencies to internal or external libraries exist.
The assessments of the person responsible in each case were collected in a structured manner and combined at a later date.
The insights gained in this way or any unclarities were then discussed in the team.
Afterwards, open questions were discussed with a Vula author and the further procedure was defined.
On a virtual test environment, an IPv6 practical test of the most current version (at that time) was performed.
In order to achieve the desired benefits for future updates and thus to future-proof this analysis, existing IPv4 tests were extended to include IPv6.

### Changes in the Codebase

To make sure that this analysis will remain helpful in later versions of vula, we extended the already existing doctests. 
Every doctest containing an IPv4 address was duplicated, exchanging the IPv4 with an IPv6 address, to check whether this test will also be successful. 
The only exception is the test of the class "Descriptor" in the file peer.py, as we weren't able to get a valid signature.
 
For the eight functions that certainly won't run with IPv6, comments were added suggesting that this function needs enhancement to support IPv6.

### Host model research

In computer networking, a host model is an option of designing the TCP/IP stack of a networking operating system.

Weak host model and strong host model are being distinguished. With the weak model, an IP packet is forwarded when the destination address does not match the address of the interface it arrives on.
In the strong host model, a system cannot send or receive any packets on an interface unless the destination IP in the packet is assigned to the interface.

Linux uses the weak host model for IPv4 and the strong host model for IPv6.

To test whether the current way Vula handles network traffic, we set up a test environment consisting of two Ubuntu 21.10 machines with the current public version of Vula installed. In a first step we assigned link-local IPv6 addresses to the physical interface and modified the routing table to route all link-local traffic over the Vula interface.

In a second step we added non-link-local addresses from the same subnet to the physical interfaces and modified the routing table to send all traffic for the subnet over the Vula interface.

Testing connectivity was done using Ping while monitoring the network traffic with wireshark.

### Results

#### Manual code review

Generally, most code seems to be IPv6 compatible, thanks to the flexible libraries.

These problems have surfaced though:

|file           | function                     | comments                                                               |
|---------------|------------------------------|------------------------------------------------------------------------|
| constants.py  | IPv4\_GW\_ROUTES             | IPv4 specific constant                                                 |
| organize.py   | action\_ADJUST\_TO\_NEW\_SYSTEM\_STATE | Usage of IPv4 only constant.                                           |
| organize.py   |  action\_REMOVE\_PEER            | Usage of IPv4 only constant.                                           |
| peer.py       | Peers.with_ip                 | Usage of IPv4Address data type                                         |
| prefs.py      | default                      | Hardcoded IPv4 addresses.                                              |
| syspyroute.py | sync\_peer                     | Usage of IPv4 only constant.                                           |
| syspyroute.py | remove\_unknown                | Hardcoded IPv4 addresses.                                              |
| wg.py         | set                          | IPv6 incompatible string splitting of IP and port (splitting with ':') |

As a result, according commentary was added to the above functions in commit 633678d2023fe1bc2531ac00c44887245a01cf5f

All other functions / methods are ipv6 compatible according to the analysis of the team.

#### Manual analysis of libraries
##### Problematic libraries
In the end, the manual analysis only found 1 problematic library: zeroconf.

The author specify that their IPv6 support is relatively new and has certain limitations. Especially listening on localhost (::1) does not work.

##### Unproblematic libraries
The following libraries are fully ipv6 compatible:

* future
* base64
* click
* click.exceptions
* copy
* cryptography
* cv2
* datetime
* dbus
* doctest
* functools
* gi.repository
* hashlib
* hkdf
* inspect
* io
* ipaddress
* json
* logging
* nacl.encoding
* nacl.exceptions
* nacl.signing
* os
* packaging.version
* pathlib
* pdb
* platform
* pydbus
* pygments
* pyroute2
* pyroute2.netlink
* pyzbar.pyzbar
* qrcode
* schema
* shutil
* sibc.csidh
* socket
* sys
* systemd
* threading
* time
* traceback
* typing
* yaml

#### Host model research

One of the open research questions regarding IPv6 and Vula is whether Vula can work within the IPv6 networking stack.

After extensive testing, we achieved the following results:

* We verified connectivity with our test setup without changing any network parameters
* Connection test were successful using link-local addresses without routing over the Vula interface
* No successful connection after changing the routing table
* Connection tests were successful using non-link-local addresses without routing over the Vula interface
* Connection tests were successful after changing the routing table 

Based on the results above we've reached the following conclusions:

* Vula should work in a network with a public IPv6 range
* Due to the way Vula handles network packets currently, it doesn't work in a link-local environment (fe80::/7 address range)
* For Vula to work in a link-local environment, major changes to how Vula handles peers and their addresses are required

Our research led to the following hypothesis:

Since addresses within the link-local range are not unique, they aren't suitable for the way Vula handles network traffic. Specifically routing packets over the Vula WireGuard interface puts those packets out of scope which in turn means the kernel will discard said packets. This means that either Vula will only work in a IPv6 network with a public range, Vula will have to change the way it handles IPv6 packets or the encryption of IPv6 packets will need to happen inside of Vula without involving the network stack.

### Conclusion

By applying our planned approach of manually reviewing the Vula code and included library plus adding automated doctests, we were able to identify eight functions that are currently not IPv6 compatible.
Comments were added to these functions to indicate that these functions need some work before they’ll work with IPv6. 

In conclusion, this project wasn’t an easy task and demanded a big learning curve for most of us in terms of IPv6 and Python. 
But once the missing knowledge was acquired, we were able to develop our results quite quickly thanks to good communication and regular meetings within the team. 

