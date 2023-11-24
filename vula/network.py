"""
Note: This module is currently unused.

>>> Network(essid={"a":True})
essid:
  a: true
<BLANKLINE>
>>> n = Network(bssid={"aa:bb:cc:dd:ee:ff":True})
>>> n
bssid:
  aa:bb:cc:dd:ee:ff: true
<BLANKLINE>
>>> bytes(list(n.bssid.keys())[0])
b'\xaa\xbb\xcc\xdd\xee\xff'
"""
from schema import Optional as Optional_
from schema import Schema

from .common import BSSID, ESSID, MACaddr, schemattrdict, yamlrepr


class Network(schemattrdict, yamlrepr):

    schema = Schema(
        {
            Optional_('essid'): {ESSID: bool},
            Optional_('gateway_MAC'): {MACaddr: bool},
            Optional_('bssid'): {BSSID: bool},
        }
    )
