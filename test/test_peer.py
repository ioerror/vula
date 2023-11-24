import unittest
from base64 import b64decode, b64encode
from ipaddress import IPv4Address, IPv6Address

import schema

from vula.common import yamlrepr
from vula.peer import Descriptor


def desc(vk, addrs, hostname, **kw):
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
    )
    data.update(vk=vk, addrs=addrs, hostname=hostname, **kw)
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


desc_str = (
    "addrs=10.215.167.50; c=KNDxDMgmkH8Poa7TJBlIZrvTnQBN5w10gYlyY5"
    "MfvkA7Eu12IhpheCdJzWIwap4PE5Ryv3PzvU4ikrEY6oXJNw==; dt=86400; e=0; "
    "hostname=wg-mdns-test1.local.; pk=y9bQa4DAj4NT5lh8PffyAbXNbYCkxczMKLk/r"
    "tP4CVY=; port=5354; r=; s=YJqLUPrI8G/IfA1wIbW2z5p0EtYcDFh4gxCjP5czMK2wi"
    "GRgZdeBibs6shDoRusfHtSy+4m/Z9Jfhul+amQYAQ==; vf=1605737957; vk=XGQErb1N"
    "Jmg4dMLZK7hXfhRahgZ6ix/oP3+BTq2+Dy8=;"
)


class TestDescriptor(unittest.TestCase):
    def test_descriptor_addrs_validate(self):
        d = desc(hostname='alice.local', vk=mkk('1'), addrs='10.0.0.255,::0')
        self.assertEqual(d.IPv6addrs, [IPv6Address("::0")])
        self.assertEqual(d.IPv4addrs, [IPv4Address("10.0.0.255")])
        with self.assertRaises(schema.SchemaError):
            desc(hostname='alice.local', vk=mkk('1'), addrs='10.0.0.256')

    def test_descriptor_parse_roundtrip(self):
        self.maxDiff = None
        desc = Descriptor.parse(desc_str)
        self.assertEqual(desc_str, str(desc))
        self.assertEqual(
            str(yamlrepr(desc)),
            """\
r: ''
addrs: 10.215.167.50
c: KNDxDMgmkH8Poa7TJBlIZrvTnQBN5w10gYlyY5Mfvk"""
            + """A7Eu12IhpheCdJzWIwap4PE5Ryv3PzvU4ikrEY6oXJNw==
dt: 86400
e: false
hostname: wg-mdns-test1.local.
pk: y9bQa4DAj4NT5lh8PffyAbXNbYCkxczMKLk/rtP4CVY=
port: 5354
s: YJqLUPrI8G/IfA1wIbW2z5p0EtYcDFh4gxCjP5czMK"""
            + """2wiGRgZdeBibs6shDoRusfHtSy+4m/Z9Jfhul+amQYAQ==
vf: 1605737957
vk: XGQErb1NJmg4dMLZK7hXfhRahgZ6ix/oP3+BTq2+Dy8=
""",  # noqa: E261
        )

    def test_verify_signature(self):
        desc = Descriptor.parse(desc_str)
        self.assertEqual(desc.verify_signature(), True)
        desc = Descriptor(desc, port=desc['port'] + 1)
        self.assertEqual(desc.verify_signature(), False)
        desc = Descriptor(desc, port=desc['port'] - 1)
        self.assertEqual(desc.verify_signature(), True)


class TestPeerShow(unittest.TestCase):
    """
    This is a doctest-style test so that we can use click.echo to strip the
    ansi escapes.

    The .replace() in the test is to handle the condition where the clock rolls
    over to the next second while the test is running.

    >>> import click
    >>> import time
    >>> peer = desc(
    ... hostname='alice.local', vk=mkk('Alice'), vf=time.time(),
    ... addrs='10.0.0.1').make_peer(pinned=True,
    ... _allow_unsigned_descriptor=True)

    >>> click.echo(peer.show().replace('1 ago', '0 ago'))
    peer: alice.local
      id: Alice/////////////////////////////////////8=
      warning: wireguard peer is not configured
      status: enabled pinned unverified
      endpoint: 10.0.0.1:1234
      allowed ips: 10.0.0.1/32
      latest signature: 0:00:00 ago
      latest handshake: none
      wg pubkey: pubkey////////////////////////////////////8=
    >>> stats = dict(rx_bytes=1, tx_bytes=50_500_000_000,
    ... latest_handshake=int(time.time()))
    >>> click.echo(peer.show(stats).replace('1 ago', '0 ago'))
    peer: alice.local
      id: Alice/////////////////////////////////////8=
      status: enabled pinned unverified
      endpoint: 10.0.0.1:1234
      allowed ips: 10.0.0.1/32
      latest signature: 0:00:00 ago
      latest handshake: 0:00:00 ago
      transfer: 1 B received, 47.03 GiB sent
      wg pubkey: pubkey////////////////////////////////////8=
    """


# fmt: off
class TestDescriptor_qrcode(unittest.TestCase):
    """
    >>> print(
    ...     '    '
    ...     + desc(
    ...         addrs='1.2.3.4', hostname='vula-qrcode-test', vk=mkk('vk')
    ...     ).qr_code.strip()
    ... )
        █▀▀▀▀▀█ █▄▀▀▀ ███▀█ █▄▀▄ █▄▀▀▄▄ ▀▀▄   █▄ █ ▀ █▄▀█▀  ▄▀█▄███  ▀█ ▀ █▀▀▀▀▀█    
        █ ███ █ ▀▄  █▀▄▄█▀ █▀▄█ ▀█▀▀ █▄███ ▄▄▀▀▄▄ ▀▄█▀ ▀ ▀▄█  █▄ ▀█  ▄▄▄  █ ███ █    
        █ ▀▀▀ █ ▀ ▄▀█▀ ██▀▀█▄  ██▀▀▀█ ▄▄▀▀▀  ▀▀▄ ▄ ▄█▀▀▀█  █████▀▀▄▄▄▄▄▀▀ █ ▀▀▀ █    
        ▀▀▀▀▀▀▀ ▀ ▀ █ █▄▀ █▄█ ▀ █ ▀ █▄▀▄▀▄█ ▀ ▀ █ ▀ █ ▀ █▄▀▄█ █ ▀ ▀▄▀ █▄█ ▀▀▀▀▀▀▀    
        █  ▀▀▀▀█▀▀ ▄▀▀ ▄▀ █▀▀ ▄ █▀▀▀▀█▄  █ ▀▀▄  ▀▀ ▀▀█▀▀█▀█ █▀▀ ▄▀▀ ▀ ██ ▀ ▄▀▄█▀▀    
        █ ▀▀█ ▀▀▄▄█ ▀ █▀█ █ █▄  ▄▄▄█▄  ▀██▀▄▀██  █ ▀█▄▄▀▀█ ▀▀ ▄▄ ▄ ▀ █▄  ▄  ▀ ▀▄     
        ▄▄▄▀▄▀▀█  ▄▀ ▀ ▀ ▀▀▀  █▀  █▀▄▄▄▄▀█▄ ▀ ▀ █  ▄▀▄  ▀█▀█▄▀▀ ▀▀█▀ █▀▄▀█▀▄█▄ ▄     
         █ █▄▄▀▀  ██ ▀▀ █ ▄█▀▀█   ▀███   █ █▀▄ ▄▀▄   ██▀██▀█ ▄ ▄▄█ ▄▀█▀▄▄▀▀▀▀  ▀▀    
        ▄ ▄ ▄█▀▄████  ▄▀█  ▄▄█ █▀████▀ ▀██▀▀▀▄▄▀ ▀ ██  ▀▄ ████▀▄ ▀ ██ █▄█ ▀▀▄ ▀▀     
          ▄▄▀█▀▄▄ █▄ ▀▀ ▀▄▀▀▄▀▀▀ ▄▄ ▀▀▀ █████▀█▄ ▀██▀▄█▄ █ ▀▄▀ ▄ ▀▄▀ ▀ ▀▄ █▀ █ ▀█    
        ▀▄ ▀█▀▀▄▀█▄▄▀  ▄▀█ ▀█▄▄ █████▄██▄▄█▄█▀▄██ ▄▄█▄▀▀▀▀█▀█ █▀▄▀  █▀▀ ▄█▀▀▄█▄█▀    
         ▀ ▄▄▀▀▄█ ▀█▄▄▄   ▀█▄▀█▄▀▀▄▄█▄▀ █  ▀█▀▄█ █ ▄▀▄ █ █  ▀ ▄▀▄▄ ▄ ▀█▀ ▄█▄ ██▀█    
         ▀▀██▀▀▀██  ▀▄▀▀ ▄ ▄ ▄ ██▀▀▀███▀ █▀▄▀▀█▀▄████▀▀▀█ ▄▀▀█ ██▀█▀██  █▀▀▀██ ▀█    
         █ ██ ▀ █   ███▄▀ █▄ █ ▄█ ▀ █▀▀▀▀ ▀██  ▄ ▀▀▄█ ▀ █ █▄▀  ▄▀ ██▀▄█▀█ ▀ ██▄█▀    
        ▄█  █▀▀▀█ █▀▄▄▀█▀    █▀█▀█▀█▀▀█▄▄█▄ ▀▄▀▀▀▀█▀████▀▀ ▀██▄ ▄ ██▀ ▀████▀▀█▀▄█    
         ▄██ █▀ █▀ ▀ ██▀█ █ ▄▀▄▀▄▀ ▄▄▄█▀ ▄▀▄▀▄█  ▄█▀   █ ▄ ▀█▄ ██▄  █  ▄▀███▀ ▀▄▀    
        ▄█▄██▀▀█ ▄▀▄▀██▄ █▀██▄▄█▀ ▀████▀▀████▄▄ ▄██ ▀▀▀  ▄▀▄▀▀  ▀▄▄▄██▀▀▀  █   ▀▀    
         ▀▄███▀▀▄██▄ ▄█▀▀▄ ▄▀██▀  ▀▄█▄▄█▄█▀  █▄▄ ▀ ▄ █  ▀▀█ ▀▄ █  █▀▀ ▄▄▄▄▄▄  ██▄    
        ▄▀▀▄▄█▀▄▀  ▄▄ █  ▄▄▄ ▀ ▄▀▄▀▀▄ ██ ▄ ▄█▀  ▄▄▀▀▄▀▄█  ▄▄    ▄▄██  ▀▀█ ▄ █▀▄██    
        ██ █▀▄▀ ▀▄ ▄█▀▄▀█▄ ▄▄██▀  ▄▄█▄█▄▀▄ ▀ ▀█▀ ▀▀██▄▀  ▄ █▄█▄█▀▀ ▄ ▄ ▀▄▄▀███▄█▄    
        ██  ▀█▀▀█  ▀▄▄▀▄▀█     █▄▀█▄ ▄ █▀▄█ ▀▀▀█▄▀▀█▄▀  ▀█ ▄  ▄ ▄▀  █▀▄█  ▀█▀ ▀ ▄    
        ▀▄▄▀▀█▀   ▄ █▄█▄▄▀▀ ▄▄▄ ▄▄▀  ▄▄▄▄ ▄▀█ ▄▀▀█ █ █▄▀▄█▄ █▀▄▄▀██▄▀▄ ▄ ▄▄█ ▄▄▄▄    
        ▀ ▀▄█▀▀▀█▀  █▄▀▀▄█ █▀▄▀▄█▀▀▀██▀▄ ▄ █▀ ▀▄▀█▄▄█▀▀▀█▀██▀▀▀█  █▄█ █ █▀▀▀█ ▀█▄    
        █ ▀██ ▀ █▀ ▄█▄ ▄ ▀█▀ ▀ ▄█ ▀ █▀▄▀▀  ▄██  ▄  ▄█ ▀ █▀▄█▀▄▀▄█ █▀▀▀▄▄█ ▀ ███ ▀    
         ██▀▀█▀██▄ ▀█ ▄ ▄▀▀ █ ▀ ▀▀▀█▀▄▀ ▀▄▄▄▀▄ ▄█▄▄▀▀▀▀▀█▄ ▄▀   ▄ ▄█▄▄  ██▀▀█▀█▄▀    
        ▄  ▄█ ▀▄  ▀█▄▀▀▀ █▀ █ █▀▀█▀ █ ▄ ▄ █▀▀ █ ▀▀▄█▄▀ ▀▄▀█▄  ▄▄█▀▄██▀█▄▄█▀▄▀█  █    
        ▄▄▄▄▄ ▀▄▀▀▄███▀ ▀ ▄█▀█ ▀█ █▄▀▄███ ▄▄█▀▀█ ▄██ ▀▀▄▄▀▄█▀▄  ▀ ▀▀▄▀▄█  ▀█▀▄▀▀▀    
        ▀▄ ██▀▀▄▀▀█▄ ▀ ▀ ▄█▄ ▄▀██▄█ ▄ ▀▄█ █▀█▄▀▀▀▄▀▀██  ▄▀▄▄██▄▀▀█ ▄▀█▄ ▄█  ▄█▀▄▀    
        ▄█ ▄█▀▀▄ ▀▀█  ▀▀▄▀▄█▀▄█▄█▄▄ █ █ ▀▄█▀  █   ▄▄█▄ ▀  ██▀ ██ ▀ ▄▀▀▄█▀█▄▀▄▀ ▄█    
         █▄█ █▀▄ ▀  █▄█ ▄ █▀ ▄▄ █ ▀ ▀█▀█▄     ▄ ▀▄   █▀▄▄█ █ ▄▄▄█  ▀▀▀█▄ ▀█ ▀█▄ █    
        █▄▀▄▄ ▀█▀▀█▄▀▄  █ ▄█ ▄▀███▀ ▀█  █▄▀   █▄ ▄█▄█▄▄ ▀ ▀██▄ ▀▀▀▀█▀▄█▄▄ ▀ ▄ ██▄    
        ▀▀ █▄▀▀ ▀▄██▀▄    ▀▄ ▄▀█ ▀▀█▄█ ▄▀ ▀▄    ▀▀▀█  ▀ ▀█▀█▀█▀█ █▄▄▀▄█▀ ▀▀▄ ████    
        ▀   ▀ ▀ █▄   ▄▀▀█ ▀▀█ ▀ █▀▀▀██ █▀▄▄▄ █▀▄█ █▄█▀▀▀██▀█▄▄█ █▀▄█ ▀▀▄█▀▀▀█▄ ▀▄    
        █▀▀▀▀▀█ █▀█▄▀██▀▀ ▀ ▀█▀▄█ ▀ █▄ ▄ ▄▀█▄▄█ █▄▀ █ ▀ █ ▄    █▄▄▄▀▀▄▄▄█ ▀ █ ▀▄█    
        █ ███ █ █▄█▄█▄██▄▀ ▀▄▄███▀▀▀▀  ▄█ ██ ██  ▄█ ▀█▀▀█▄▄▀▄▄ ▄ ▄▀ ▀▄▀▀███▀█ ▄ ▄    
        █ ▀▀▀ █   ▄▀█ ▀█▄ █▀▄█▄▄▀▀ ▀█  ▀███▀█ ▄█▀▀▄█ ▄ ██▀▄██▄▄▀▀▀▀██▀█  ▀▄▀██▄██    
        ▀▀▀▀▀▀▀ ▀ ▀▀▀  ▀▀ ▀▀▀▀  ▀▀▀  ▀    ▀    ▀     ▀ ▀▀ ▀ ▀  ▀  ▀▀▀ ▀ ▀▀  ▀   ▀
        """
# fmt: on


if __name__ == '__main__':
    # this is here to be able to run this file by itself, like this:
    #       python -m tests.test_peer
    # (these tests are usually run with pytest, however.)
    import doctest

    print(doctest.testmod())
    unittest.main()
