import unittest
from base64 import b64decode, b64encode
from ipaddress import IPv4Address, IPv6Address

import schema

from vula.peer import Descriptor


def desc(vk, v4a, hostname, **kw):
    "make test descriptor"
    data = dict(
        pk=mkk('pubkey'),
        c=b'a' * 64,
        port=1234,
        dt=0,
        vf=0,
        s=mkk('signature', 64),
        e=False,
        r='',
        p='fdff::1',
        v4a='10.0.0.1',
    )
    data.update(vk=vk, v4a=v4a, hostname=hostname, **kw)
    return Descriptor(data)


def mkk(n, length=32):
    """
    make human-readable base64 key-shaped strings. argument must consist of
    base64-allowed characters.

    >>> mkk('Hello')
    'Hello/////////////////////////////////////8='
    >>> for i in range(2,100):
    ...     for j in range(1,i):
    ...         assert len(b64decode(mkk('x'*j, i))) == i
    """
    n = str(n)
    b64len = 4 * (length // 3 + (1 if length % 3 else 0))

    assert 0 < len(n) < length
    return b64encode(b64decode(n + (b64len - len(n)) * '/')[:length]).decode()


class TestDescriptor(unittest.TestCase):
    """
    Tests for descriptors.

    Note there are many more, in the form of doctests.
    """

    def test_descriptor_addrs_validate(self):
        d = desc(
            hostname='alice.local',
            vk=mkk('1'),
            v4a='10.0.0.255,1.2.3.4',
            v6a='::0',
        )
        self.assertEqual(d.IPv6addrs, [IPv6Address("::0")])
        self.assertEqual(
            d.IPv4addrs, [IPv4Address("10.0.0.255"), IPv4Address("1.2.3.4")]
        )
        with self.assertRaises(schema.SchemaError):
            desc(hostname='alice.local', vk=mkk('1'), v4a='10.0.0.256')


class TestPeerShow(unittest.TestCase):
    """
    This is a doctest-style test so that we can use click.echo to strip the
    ansi escapes.

    The .replace() in the test is to handle the condition where the clock rolls
    over to the next second while the test is running.

    >>> import click
    >>> import time


    Test a peer with only the IPv6 ULA:

    >>> peer = desc(
    ... hostname='alice.local', vk=mkk('Alice'), vf=time.time(),
    ... v4a='', v6a='', p='fdff:ffff:ffdf::1').make_peer(pinned=True,
    ... _allow_unsigned_descriptor=True)
    >>> click.echo(peer.show().replace('1 ago', '0 ago'))
    peer: alice.local
      id: Alice/////////////////////////////////////8=
      warning: wireguard peer is not configured
      status: enabled pinned unverified
      endpoint: 0.0.0.0:1234
      primary ip: fdff:ffff:ffdf::1
      allowed ips: fdff:ffff:ffdf::1/128
      latest signature: 0:00:00 ago
      latest handshake: none
      wg pubkey: pubkey////////////////////////////////////8=

    Change the stats:
    >>> stats = dict(rx_bytes=1, tx_bytes=50_500_000_000,
    ... latest_handshake=int(time.time()))
    >>> click.echo(peer.show(stats).replace('1 ago', '0 ago'))
    peer: alice.local
      id: Alice/////////////////////////////////////8=
      status: enabled pinned unverified
      endpoint: 0.0.0.0:1234
      primary ip: fdff:ffff:ffdf::1
      allowed ips: fdff:ffff:ffdf::1/128
      latest signature: 0:00:00 ago
      latest handshake: 0:00:00 ago
      transfer: 1 B received, 47.03 GiB sent
      wg pubkey: pubkey////////////////////////////////////8=

    >>> peer = desc(
    ... hostname='alice.local', vk=mkk('Alice'), vf=time.time(),
    ... v4a='10.0.0.1', v6a='::1').make_peer(pinned=True,
    ... _allow_unsigned_descriptor=True)
    >>> click.echo(peer.show().replace('1 ago', '0 ago'))
    peer: alice.local
      id: Alice/////////////////////////////////////8=
      warning: wireguard peer is not configured
      status: enabled pinned unverified
      endpoint: [fdff::1]:1234
      primary ip: fdff::1
      allowed ips: fdff::1/128, ::1/128, 10.0.0.1/32
      latest signature: 0:00:00 ago
      latest handshake: none
      wg pubkey: pubkey////////////////////////////////////8=

    Test a peer with an IPv4 primary_ip:
    >>> peer = desc(
    ... hostname='alice.local', vk=mkk('Alice'), vf=time.time(),
    ... v4a='10.0.0.1', p='1.2.3.4').make_peer(pinned=True,
    ... _allow_unsigned_descriptor=True)
    >>> click.echo(peer.show().replace('1 ago', '0 ago'))
    peer: alice.local
      id: Alice/////////////////////////////////////8=
      warning: wireguard peer is not configured
      status: enabled pinned unverified
      endpoint: 1.2.3.4:1234
      primary ip: 1.2.3.4
      allowed ips: 1.2.3.4/32, 10.0.0.1/32
      latest signature: 0:00:00 ago
      latest handshake: none
      wg pubkey: pubkey////////////////////////////////////8=
    """


# fmt: off
class TestDescriptor_qrcode(unittest.TestCase):
    """
    >>> print(
    ...     '    '
    ...     + desc(
    ...         v4a='1.2.3.4', hostname='vula-qrcode-test', vk=mkk('vk')
    ...     ).qr_code.strip()
    ... )
        █▀▀▀▀▀█ ████▄▄█▄▀█▄▄███▀▄ █▄▀▄▀█ ▄ ▄▀█  ▄▄█ ▄  █▀▀   ▄▀▄▀▄█ █▄█ ▀ █▀▀▀▀▀█    
        █ ███ █ ▀██   ████  ▄▀ ▀ ▄  ▄▀ ▀█▄▄▀▄█▀█▄   █▀▄▄▀█▄▄▄▀▀█▀▄██▀▄▄▄  █ ███ █    
        █ ▀▀▀ █ ▀█   ▄ █ ▄ ██ ▄ █▀▀▀█▄ ▀▄▄█▀▄ ▄▄ ▄█ █▀▀▀█ ▀▄█▀ ▄ ▄  ██▄▀▀ █ ▀▀▀ █    
        ▀▀▀▀▀▀▀ ▀▄█▄▀ █ ▀ █ █▄▀ █ ▀ █▄█ ▀▄█▄▀ ▀ █▄▀ █ ▀ █ █ █ ▀ ▀ █▄▀ █ ▀ ▀▀▀▀▀▀▀    
        ▀▄ ▀██▀▀██▄██ ▄  █▀▄▄██▄█▀▀██▀ █▄▄▄ ██▀ ██▀█▀█▀▀█▀▀▄█▀▀ ▄▀▀▀█ █▀ █▄▄▀▄██▀    
           █ ▄▀ ▀█▄▀ █  ▄█ ▀ ▀▄▀▄▄ ▄   ▀ ▄▀██  ▀▄ █▄▀  ▄▄▄▄█▄ ▄ ▄▄ ▀▄█▄   ▀▀▄▄█ ▀    
        ▄▀▀█ ▀▀▀▀██▄▄▄▄▀▄██▀██▄▀ ▀█ ▀▀  ▀▄▀▄▀█▄▄█▀ ██ ▄ ▄██▄ ▀█▀ ▀▀▄▀██▀▄█▀▄▄▄ ▄▄    
        ▀▄█▄▀▀▀▀▀▀▀▄▄▀ ▄▄▄▀▄▄▄██ ▄██▀▀▄ ▄ ▄▀█▀▄ █▀▄▄  ▄▀ █▀▄▀▄ █▀█ █ █▀ ▄▀▀▄ ▄▄▀▄    
        ▀▄▄ ▄▀▀█▄█▀█ ▄███▄  ▀▄▀ ▀█▄█▀▄███ ▄ ▀▀▀▄ ▄█▀▀▄ ▀█ ▀█▀██ ▄▀▄▀▀ ▀ █▀▄██▄▄▀▀    
        █▄█ ▀ ▀█ ▄█   ▄▀▀▄ ▄▄▄█▄▀  █▀▄█▄█▄▀ █ █ ▀▄█ ▀▄█▄▄█ ▄█▀  ▀▀▄█▀▀ ▀▄▄█ ▄█ █▀    
        █▄▀▀▄ ▀▄█ ▄▄█▄▄ ▀█▀▄▀█▄ ▄▄▄▀▀▄▄ ▀█▄▀ ██  ▄▄ ▄█  ▀▀██▀ ▀█ ▀ ▄▀▀▀  ▄▄▀ █▄      
        █ ▀▄  ▀▄ ▀█▄▄ ▄   ████▄▀█▀▀█▄▀▄▀▄██ ▄▄ ▄▀▀▄▀▄██▄██ █   ▄█▄█▀▀█ ▀█ █▄ ▄█▄█    
        █▀▀ █▀▀▀█▄▄  ▀█▀█▄▄▀ █▄▀█▀▀▀██▄ ▄█ ▄ ▀▄▀▄█▄ █▀▀▀█▄ ██▄▄▀▀█▄█▀█▀▄█▀▀▀██▀██    
        █▀▄██ ▀ █▄██▄██ ▀▄▄▀▀▀███ ▀ █ ▄▄▄▀   ██▄█▄ ██ ▀ █▄▀█▄▀▄█▀▀ ▄▀ ▄██ ▀ █▄▄██    
        █ ▀▄██▀██▀ █▄██  ▄█▀ ██▄▀▀▀█▀███  █▀ ▄▀▄ ▄█▀██▀▀██ ██▄▄ ▄▀██▀▀ ▀█▀██▀▀ ▀▄    
        ▀██▄█▀▀▄▄ ██ ▀  ▄█▄ ▄ ▄▀█▀█▀▄ ▄ ▄▀▄█  ▄▄█  ▄ ▄█▄▄▀ ▀█  █ ▄▄▄▄ ▄█ ██ ▀█▀▄█    
        ▀▀▄▄▄▀▀  ██ █ ▀▄▀  ▀ ▀▄▄▄▄ ▄▄▄█▄ ▀▄  ██▄█▀▄▄▄█ █▀▄ ▀▀█ ▄█  █ ▄██▄ ▄▄ █       
         ▀█▄▄ ▀ ▄ ██▄█  ▀ ▀█▀ █▄▀▀▄ ▄▄ ██ █  ▄▄▄▀▀ █ █▄ █ ▄▀▄▄▀█  ▀█▄▀ ██▀▄▄▀▄▄█▄    
        ▀▀▄█ ▄▀██▄ █▀ ███ ▀▀ █▀▀█ ▄▄ █▄██ ▀▀  ▄▄▀█ ▀▄▀▀█▄▄▄█▀ ▀▀▄ ██▄▄▄█ ▀ ▄█▄▄█▀    
        ▀▄▄▀▄ ▀█ ▀█ ▄ ▄▀█ ▄▄▀█ █▄  ▀▄▀ █ ██▀ ▄▀▄  ▄▀▀█ █▀ █▀ ▄▄██ █▄ █ ▀▄▄▄███ ▀     
        ▄ █  █▀█▄▀█▀  ▄▄▀█▀▀▀▀▀██▀██   ▄▀ ▀▄▀█ ▀▄▄██ ▀▄   ▀█▀ ▀██ ▀█ █ █ ▀▄▀▀██▀▄    
         █▀█▄ ▀▀▀███▄ ▄▄ ███  █ █▄██  ▀▀▀▄ ▄▀▄ ▀█▄▄ ▀█▄▀ ▀█▀▄ █▄▀█▄ ▀▄▀▄   █ ▄█▄▄    
         ████▀▀▀█▀█▀█▄▄▄█▀▀▀▄▄▄▀█▀▀▀█▄▄█▄▄▀▄█▄▀█▀▀ ▄█▀▀▀█▀ ▄▀▀▀█  █▄▀ █▄█▀▀▀█▀▄ ▀    
        ▀▄▄ █ ▀ ██▀▀██▄█▀█ █▄▄▀██ ▀ █▀▀█▀▀▀ ▄█▀██▄▄▄█ ▀ █▄▄█▀ ▀▄▄▄█▀▀█▄▄█ ▀ █▄▀▀     
        ▀ ██▀▀▀▀█▄▀ █▀▄█▀▀▀  ▀██▀█▀█▀▄▀ █ ▄▄█▄█▄▀▄ ▄█▀▀███▀▀▄▀▀ █▀█▄▄█▀███▀▀█▄█▀     
        █▄▄█▀▀▀▄██▄▄  ▄█▀▄█ ▀▄  ▄ ▀▀▀█▀███ ▄▄▄▀█▄█▀▄▄▀▀  █▀▄▀▄ ▄▄█ █ █▀█  ▀▄▀█ ▀▄    
        █▀▀█▀▀▀████ ▀▄ ▄ ███▄▀▄▄▄▀  █▀ █▀█▀ █▄▄▄▄▀ ▀█▀▀▄▄ ████▀  ▀ █  ██▀█████▀█▀    
        ▀▄▄█▄▄▀ ▄▄▀█▀▄█▀ █▀ ▀▄ ███▀ ▄██▀▄▀██▄█▀█ ▀▀ ██▄▀ █ ▀█▀ █▀█▄ ▀█ ▄▀█ ▄ █▀ █    
        █▄▄ ▀▄▀█▀ ▄▀ █▀▄   ▀███ ▄█ ▀ ▄▄█▄██▄██▄██▄█  █ ▀▄▀▀█ ▀██▀▀▄▄ ▀▀▄▀  ▄ █▄ ▀    
        █▄   █▀▀▄█▀  ▄▀▀█▄█▄█▄ ▀█▀█ ▀▀▀▄█  █▀▀█▀ ▄▀█▀▄██ ▀▀▀  ▄ █ ██▀▀██▄▀█▀ ██▀▀    
        ███  ▀▀█▄███ ▄▄ █ ▀ ▄▀█▄▄▄█▄ ▄█ ▀█▀  ▀█▄███▄▀▄   ▀ █▄▄▀▀ ▄▄█ ████ ▀▄ █ █▄    
        ▀▀ █▄▀▀▄▄▀▀▀    ▀ ▄▀█   ▀▀█ ▄▀▄▄▀ ██ ▄▄▄▀█▀▀▄▄▀ ▀▄██▀▄ █ ▄▀▄▀███▄█▀█▀█▄▀█    
        ▀   ▀ ▀▀███▀▀ ▄ █ ▀▀▄█▀ █▀▀▀███ ▄█▄ █ ▀ ▀▄█ █▀▀▀█▄ █▄ █ █ ▄█  ▀ █▀▀▀██▀▀▄    
        █▀▀▀▀▀█ █▄ ▀ ▀▀▀█ █▄▄  ▀█ ▀ ███  ▀▄   ▄█  ▄██ ▀ █▀▄▄▄▄▄▀▀ ▄▀   ▄█ ▀ █▄  █    
        █ ███ █ █ ▀█▄██ ▄▄ ▀▀▄▀█▀█▀█▀▀  ▀▀▄█▄█▄▄ ▄█▀█▀█▀█▀▀█ ██▄ █ ▀ ▄ ▀▀██▀▀ ▄ ▄    
        █ ▀▀▀ █  ▀▄▄▄███▄▄▀   ▀█▀▀▄██▄▄   ▀▄▀▄ █▄▄ ▄▀█▀█ ▀▄▄█▄ ██ █▄  ▄ █▀█▀ █▄██    
        ▀▀▀▀▀▀▀ ▀▀ ▀▀   ▀ ▀   ▀▀▀▀ ▀▀ ▀▀▀▀▀   ▀    ▀▀     ▀   ▀ ▀ ▀   ▀ ▀   ▀   ▀
        """
# fmt: on


if __name__ == '__main__':
    # this is here to be able to run this file by itself, like this:
    #       python -m tests.test_peer
    # (these tests are usually run with pytest, however.)
    import doctest

    print(doctest.testmod())
    unittest.main()
