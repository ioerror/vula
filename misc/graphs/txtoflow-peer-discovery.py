#!/usr/bin/env python3
# pip3 install txtoflow
from txtoflow import txtoflow

txtoflow.generate(
    outFile='txtoflow-wg-mdns-rules.jpg',
    code='''
    Organizer has a database of Peers;
    Organizer waits for mDNS broadcasts with a Peer Descriptor;
    Organizer receives a Descriptor;
    Organizer filters Descriptor IP addresses which are not local to Organizer;
    if (Descriptor Public Key in Organizer cache) {
        if (Descriptor contains signature created by Public Key) {
            if (Verify signature) {
                if (Descriptor serial number is higher than previously cached values) {
                    Update in cache;
                    Remove claim on old IP addresses;
                    Remove old routes;
                    Add new claim on new IP addresses;
                    Add new routes via wg-mdns device;
                    Add new endpoint for Descriptor Public Key;
                    Organizer waits for mDNS broadcasts with a Peer Descriptor;
                }
                Discard Descriptor;
                Organizer waits for mDNS broadcasts with a Peer Descriptor;
            }
            Discard Descriptor;
            Organizer waits for mDNS broadcasts with a Peer Descriptor;
        } else {
            Discard Descriptor;
            Organizer waits for mDNS broadcasts with a Peer Descriptor;
        }
    } else if (Descriptor IP address list contains entries which match entries in the Organizer IP address list) {
        Discard Descriptor;
        Organizer waits for mDNS broadcasts with a Peer Descriptor;
    } else {
        Add Descriptor Public Key to wg-mdns interface;
        Add Descriptor IPv4 address and port to wg-mdns endpoint for Public Key;
        Add Descriptor IPv4/IPv6 addresses to AllowedIPs for PublicKey;
        Add routes for IPv4/IPv6 addresses via wg-mdns interface;
        Add peer to Organizer peer list;
        Cache Organizer peer list on disk;
        Organizer waits for mDNS broadcasts with a Peer Descriptor;
    }
    ''',
)
