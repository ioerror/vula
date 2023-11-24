"""
*vula* CTIDH interface functions.
"""
from hashlib import sha512
from typing import ByteString

from highctidh import ctidh  # noqa: F401
from hkdf import Hkdf

from .common import b64_bytes

# ctidh field size
ctidh_parameters = 512


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
