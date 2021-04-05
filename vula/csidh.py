"""
*vula* CSIDH interface functions.
"""
from base64 import b64encode
from hkdf import Hkdf
from hashlib import sha512

from sibc.csidh import CSIDH

from .common import b64_bytes


csidh_parameters = dict(
    curvemodel='montgomery',
    prime='p512',
    formula='hvelu',
    style='df',
    exponent=10,
    tuned=True,
    uninitialized=False,
    multievaluation=False,
    verbose=False,
)


def hkdf(raw_key):
    kdf = Hkdf(salt=None, input_key_material=raw_key, hash=sha512)
    key = kdf.expand(b"vula-organize-1", 32)
    psk = str(b64_bytes.with_len(32).validate(key))
    return psk


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=1)
