"""
*vula* CSIDH interface functions.
"""
from hkdf import Hkdf
from hashlib import sha512

from sibc.csidh import CSIDH  # noqa: F401
from typing import ByteString

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


def hkdf(raw_key: ByteString) -> str:
    """
    >>> s = hkdf(b"my_raw_key")
    >>> s
    'Y52eWgiYuPYtHlnqZpRqAG2USxILzRS57s61ePUdWO4='
    >>> type(s)
    <class 'str'>
    >>> hkdf("my_raw_key_string")
    Traceback (most recent call last):
     ...
    TypeError: ...
    """
    kdf = Hkdf(salt=None, input_key_material=raw_key, hash=sha512)
    key = kdf.expand(b"vula-organize-1", 32)
    psk = str(b64_bytes.with_len(32).validate(key))
    return psk


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=1)
