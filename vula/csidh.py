"""
*vula* CTIDH interface functions.
"""

from typing import ByteString

from highctidh import ctidh  # type: ignore  # noqa: F401
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .common import b64_bytes

# ctidh field size
ctidh_parameters = 512


def hkdf(raw_key: ByteString) -> str:
    """
    >>> hkdf(b"test string")
    'P39kOvTABj0XVj0wFMcZZw1F/njgFOlJDE44i8QG2LA='
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
    key = HKDF(
        algorithm=hashes.SHA512(),
        length=32,
        salt=None,
        info=b"vula-organize-1",
    ).derive(raw_key)
    psk = str(b64_bytes.with_len(32).validate(key))
    return psk


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
