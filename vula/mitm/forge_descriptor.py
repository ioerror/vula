import datetime
import time
from base64 import b64encode, b64decode
from vula.peer import Descriptor
from nacl.signing import SigningKey
from nacl.encoding import Base64Encoder
from vula.csidh import csidh_parameters, CSIDH
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


class VulaKeys:
    def __init__(self):
        self._ed25519_keypair_gen()
        self._csidh_keypair_gen()
        self._x25519_keypair_gen()

    def _ed25519_keypair_gen(self):
        """
        Generate a seed for the Ed25519 verify keypair used by vula.
        """
        signing_key = SigningKey.generate()
        self._ed25519_private = signing_key.encode(
            encoder=Base64Encoder
        ).decode()
        verify_key = signing_key.verify_key
        self._ed25519_public = b64encode(verify_key.encode()).decode()

    def _csidh_keypair_gen(self):
        self._csidh = CSIDH(**csidh_parameters)
        sk = self._csidh.secret_key()
        pk = self._csidh.public_key(sk)
        self._csidh_public = b64encode(pk).decode()
        self._csidh_private = b64encode(sk).decode()

    def _x25519_keypair_gen(self):
        temp_key = X25519PrivateKey.generate()
        private = b64encode(
            temp_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
        ).decode("utf-8")
        public = b64encode(
            temp_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ).decode("utf-8")
        self._x25519_private = private
        self._x25519_public = public

    def get_csidh_private_raw(self) -> bytes:
        return b64decode(self._csidh_private)

    def get_csidh_private_b64(self) -> str:
        return self._csidh_private

    def get_csidh_public_raw(self) -> bytes:
        return b64decode(self._csidh_public)

    def get_csidh_public_b64(self) -> str:
        return self._csidh_public

    def get_x25519_private_raw(self) -> bytes:
        return b64decode(self._x25519_private)

    def get_x25519_private_b64(self) -> str:
        return self._x25519_private

    def get_x25519_public_raw(self) -> bytes:
        return b64decode(self._x25519_public)

    def get_x25519_public_b64(self) -> str:
        return self._x25519_public

    def get_ed25519_private_raw(self) -> bytes:
        return b64decode(self._ed25519_private)

    def get_ed25519_private_b64(self) -> str:
        return self._ed25519_private

    def get_ed25519_public_raw(self) -> bytes:
        return b64decode(self._ed25519_public)

    def get_ed25519_public_b64(self) -> str:
        return self._ed25519_public


def forge_descriptor(
    vula_keys: VulaKeys, new_addrs: str, new_host: str, port: int
) -> Descriptor:
    """
    :param vula_keys: ed25519, csidh, x25519
    :param new_addrs: 112.118.112.116, 111.118.111.110
    :param new_host: neo.local.
    :return: signed Descriptor
    >>> vula_keys = VulaKeys()
    >>> desc = forge_descriptor(
    ...     vula_keys,
    ...     '112.118.112.116',
    ...     'neo.local.',
    ...     5354)
    >>> print(desc.addrs)
    112.118.112.116
    >>> print(desc.hostname)
    neo.local.
    >>> print(desc.verify_signature())
    True
    """
    data = dict(
        addrs=new_addrs,
        hostname=new_host,
        pk=vula_keys.get_x25519_public_b64(),
        c=vula_keys.get_csidh_public_b64(),
        port=port,
        dt=86400,
        vf=int(time.mktime(datetime.datetime.now().timetuple())),
        vk=vula_keys.get_ed25519_public_raw(),
        e=False,
        r='',
    )
    desc = Descriptor(data)
    return desc.sign(vula_keys.get_ed25519_private_raw())


def serialize_forged_descriptor(forged_descriptor: Descriptor) -> dict:
    """
    serialize forged descriptor
    :param forged_descriptor: Descriptor object
    :return: dictionary containing serialized descriptor
    >>> vula_keys = VulaKeys()
    >>> desc = forge_descriptor(
    ...     vula_keys,
    ...     '112.118.112.116',
    ...     'neo.local.',
    ...     5354)
    >>> serialized_desc = serialize_forged_descriptor(desc)
    >>> isinstance(serialized_desc, dict)
    True
    >>> serialized_desc['addrs'] == '112.118.112.116'
    True
    """
    return forged_descriptor._dict()


if __name__ == "__main__":
    import doctest

    print(doctest.testmod())
