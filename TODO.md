# TODO

We should migrate everything in this TODO to codeberg issues.

- URGENT pre pypi release: determine if missing requirements.txt breaks PyPI packaging

- review Tk frontend more; fix scrolling bug there.

- move DEPENDENCY.md to contrib?

- move misc/install-mitm-deps.sh to contrib/mitm/ ?

- review HACKING.md and ensure pipenv/pipx information is relevant/working/etc (narrator: it isn't)

- setup codeberg CI

- we need to research more to figure out what our minimum requirements actually
  are, and better define a way to install everything on older systems.
  pipx? docker?


- install .desktop file for gui
- figure out what it takes to use vula with userspace (golang) wg. (does pyroute2 help?)
- delete some no-op tests from publish (and elsewhere)
- figure out what could cause a NonUniqueNameException - (post-bfh merge we
  ignore that exception now instead of crashing on it, but we don't know
  when/why it actually happens. maybe we should make systemd not stop restarting
  instead?)

- rename notclick to click or clickutils or something
- make tk frontend stop doing import *
- check if tk frontend really needs to make a tempfile or if qrcode lib can just return an image
- petnames are broken on Ubuntu 20.04 due to a permissions issue

- stop calling sync from `get_new_system_state`, triggers should handle it

- Review this TODO file, remove outdated things, and file codeberg issues for what remains.

- document considered attacks (eg: rogue DHCP servers, arp spoofing, etc)

- fix discover/organize deadlock

    - easily reproducible by running rediscover while organize is blocked in
      csidh on startup

        - organize's rediscover blocks on discover's `listen([])` which blocks on
          `zeroconf.cancel()` if there is a zeroconf thread already blocked on a
          call to organize's `process_descriptor` (which won't begin executing
          until the rediscover call is finished, which will never happen
          because it is blocked waiting for the call to discover's `listen([])`
          method)

    - this is also almost certainly triggerable by certain sequences of netlink
      and descriptor events, eg, if a descriptor comes in at the same time as
      the netlink monitor thread finds out we no longer have an IP bound.

    - root cause is fundamentally a design flaw of ours: organize and discover
      both call the other.

        - fix might be to to replace dbus method calls in one or both
          directions with dbus signals?

        - if we had the intermediate-state design for async csidh (described
          below) this bug would be much harder to trigger, but would still
          exist.

- implement encrypted `verify against` command

  - Implement an AEAD payload keyed by a DH between host keys and target
    system's keys to ensure a camera cannot meaningfully make use of a QR code
    on a screen.
  - see `bfh-verify-against` feature branch for progress toward design and
    implementation.

- async csidh?

    - the plan: make process descriptor commit quickly, before csidh is done.
      when syncing a peer with no psk, omit its endpoint to nullroute packets
      to it. when a csidh worker process completes, fire a new event and commit
      a mutation to the peer object and then resync it.

- netlink monitor thread will currently stop working if it gets an exception
  during a dbus call to publish or discover

- organize should catch the TERM signal and tell discover and publish to exit

- vula-organize systemd service should be renamed to vula

- implement auto-repair feature which automatically calls sync periodically

- investigate packaging change

    - something changed and now our deb has `python3-*` deps and the egg has
      our whole repo

- review netlink monitor

    - which events do we ignore

    - should we batch events?

        - eg, when turning off wifi, there is an event for removing the default
          route before the event to unbind the ip. currently we process those
          events separately, so we remove the use_as_gateway flag before we
          remove the peer (if it is unpinned).

- test pinned-vs-unpinned gateway roaming behavior more

- document that discover and publish shouldn't be restarted without also
  restarting organize?

    - the current situation (i think) is that organize can be safely restarted,
      and will publish a new descriptor and cause discover to (re-)discover.
      however, if publish or discover is restarted, organize will not instruct
      them until a netlink event (or an organize restart).

- unpinned peers should expire

    - this requires new descriptors to be generated and signed even if nothing
      else has changed to bump the vf value up.
    - see `bfh-expiration-of-unpinned-peer-feature` branch for progress toward
      this feature.

- we should have different events for peer and pref edits, instead of using
  `ev_USER_EDIT`, and then we should have triggers fired by the state engine to
  update just the bits we know need to be updated instead of running a full
  `sync()` for each change.

    - once this happens, we can have the full sync be optionally run
      periodically and/or after every event based on the auto_repair preference

    - this will also let us stop logging intentional peer removal/disabling as
      "unexpected"

- there should be a `vula stop` command which tells all 3 daemons to stop (via
  dbus), upon which organize can delete the interface and rules.

- dbus policy XML needs to be cleaned up a lot; currently it has lots of
  duplication and unnecessary stuff to establish some boundaries but then
  negates most of them for development.

- there should also be a prerm or postrm hook to remove our nsswitch config
  (prerm means we could make a subcommand of configure for it)

- replace `record_events` feature with an event log saved to another file
  instead of the state itself

    - add a monitor command which subscribes to event notifications via dbus
      signals or something and prints results as they happen

    - the current `record_events` feature defaults to off and hasn't been used
      it a while and may or may not still function

- add "join" command which takes a reunion passphrase as performs
  reunion-on-an-ethernet to automatically verify (and thus pin) any other peers
  using that passphrase. this will allow bidirectional pinning with headless
  peers (including routers).

    - see `bfh-reunion-integration` feature branch for progress toward REUNION
      integration.

- write a cryptographic warnings page about CSIDH similar to this one about
  ntruprime:

    - https://ntruprime.cr.yp.to/warnings.html

---

- replace wireshark screenshot (the one currently in the paper has the old
  `_wireguard._udp` name)

- validate hostname
- qrcodes
- roam to thunderbolt graph
- graphs:
  - latency
  - bandwidth

---

-  sub-command called key-gen (including VK key) / rotate-sub-keys (not VK key)
-- pre-paper deadline
-- medium

- All of vula should run unprivileged and should use polkit with dbus to
  talk to the various daemons.
-- pre-paper deadline
-- easy (just decide which functions need to be gated, see example code)

- QR code key exchange
-- pre-paper deadline
-- fun, medium
-- vula qr-verify bob || bob_vk
--- aead encrypted to the dh between self + bob ( optional + ephem key)
---- descriptor for self, and bob as plaintext payload || one hash of the last respective sig from self, and bob after sorting

-- vula qr-discover
--- qr code encoding our latest descriptor

---

- Protocol design discussion: private peer verification scheme with QR codes.
-- post-paper deadline
-- easy, fun, time consuming

- Private peer verification scheme with QR codes that resist a camera in the
  room. DH(ephemeral, peer_pk)
-- post-paper deadline
-- medium, fun, time consuming


- Documentation automatic generation with Sphynx
-- post-paper deadline
-- easy

- Continuous Documentation: automatically build, version, and host documentation with readthedocs
-- there seems to be an issue with codeberg and RTD which has to be checked: https://codeberg.org/Codeberg/Community/issues/486


- Alternative transport design
-- post-paper deadline
-- easy, boring, uninteresting, hateful

- use other CSIDH library (sidechannel free library)
-- post-paper deadline

- Website
-- post-paper deadline

- RPMs
-- post-paper deadline
-- easy

- pip3 installable objects
-- post-paper deadline

- Monolith mode: a single sub-command which runs all needed services in threads
  or processes without privilege separation.
-- post-paper deadline

- Publish service should have a limited lifetime and it should have a way to
  rotate CSIDH keys.
-- see branch `bfh-keyrotation-feature` for progress on this task.

- vula should have a sub command called proxy mode. This should allow a
  device which can use wireguard but cannot run other software to participate
  in the protocol and then it should be able to push configuration changes to
  that machine.
-- post paper deadline

---

Enable Click (bash) tab completion (!)

- built-in support is no good for multicommands, but maybe the one from contrib is?

---

Investigate the use of RFCTBD:
```
  NetRange:       100.64.0.0 - 100.127.255.255
  CIDR:           100.64.0.0/10
  NetName:        SHARED-ADDRESS-SPACE-RFCTBD-IANA-RESERVED
  NetHandle:      NET-100-64-0-0-1
  Parent:         NET100 (NET-100-0-0-0-0)
  NetType:        IANA Special Use
```

---

Consider adding IPSEC peers when WireGuard isn't supported.
```
  sudo apt install libreswan
  wget https://raw.githubusercontent.com/libreswan/libreswan/main/docs/examples/oe-upgrade-authnull.conf
  sudo mv oe-upgrade-authnull.conf /etc/ipsec.d/oe-upgrade-authnull.conf
  echo "0.0.0.0/0" |sudo tee -a /etc/ipsec.d/policies/private-or-clear
  # Add the following sysctls:
  net.ipv4.conf.all.send_redirects = 0
  net.ipv4.conf.all.accept_redirects = 0
  net.ipv4.conf.default.accept_redirects = 0
  net.ipv4.conf.default.send_redirects = 0
  sudo systemctl start ipsec
  sudo ipsec verify
  sudo ipsec whack --oppohere 192.168.2.129 --oppothere 192.168.2.130
```
via [IPsec OE](https://libreswan.org/wiki/HOWTO:_Opportunistic_IPsec)

---

Add Firewall rules for each peer to prevent leakage of IP packets when a user
accidentally brings up another vpn and local network packets would traverse the
wrong link? Any application that uses ip rules and adds a rule without a
priority, as `wg-quick` does, will cause us to leak presently.

 - iptables rule from vula IP address to peer IP address with fwmark
   allowed through, REJECT otherwise.

- Add ephemeral mode flag to publish/discover: e=0

- Announcing more complicated routes is out of scope for now but later we may
  allow a user to announce other routes. This could allow peer-by-peer NAT and
  tunnel sharing. More info required for this design idea.

- Investigate how WebRTC works these days.
    - this demo
      https://github.com/warren-bank/js-get-local-area-network-ip-address
      returns uuid-lookin' names like
      f0ac443f-5d25-493e-b368-9ac2276b8381.local now, but they don't seem to
      resolve for me. how does this work?
    - further reading:
        - https://bloggeek.me/psa-mdns-and-local-ice-candidates-are-coming/
        - https://datatracker.ietf.org/doc/draft-ietf-rtcweb-mdns-ice-candidates/

- Read and consider our relation to [Efficient Privacy PreservingMulticast DNS Service Discovery](https://www.uni-konstanz.de/mmsp/pubsys/publishedFiles/KaWa14a.pdf)

Think about combining vula with the reunion protocol. Could "reunion on an
ethernet" work via a gethostbyname interface? Maybe.

- need to install new packages on debian: python3-opencv

- Add support for OpenBSD; see TODO.porting

- Signatures should be over an exploded buffer with foo=bar; rather than just a
  concatenation of bar into a buffer. This will allow the signed buffer to be
  parsed and result in a key value pair where every byte can be used.
  Currently, we do a half-assed thing and we should do something smarter.

- Discover and publish used to throw exceptions when they lost network
  connectivity. This problem has hopefully gone away but we should carefully
  investigate what happens in various scenarios to be sure.

- For concerns regarding IPv6 compatibility consolidate README.ipv6.md

- Increase test coverage

- Add man page documentation

- Add online documentation


## Compatibility with RPM-based systems

- To add the post-installation script to the RPM build, you can append the following parameter to the bdist_rpm command in the makefile:\n
  `--post-install=misc/python3-vula.postinst`\
  The RPM package then executes the post-installation script, but the script fails at importing vula-libnss.
  When installing vula-libnss manually with `sudo pip install vula-libnss` it works again.

- When installed on Fedora and run without root privileges, vula displays the following error message:\
  `gi.repository.GLib.GError: g-dbus-error-quark: GDBus.Error:org.freedesktop.DBus.Error.AccessDenied: Sender is not authorized to send message (9)`

- When manually executing the last post-installation step on openSUSE (`sudo systemctl enable --now vula-organize`), the following error message appears:\
  `Failed to enable unit: Unit file vula-organize.service does not exist.`\
  Vula cannot be used, if the organize service doesn't run.
