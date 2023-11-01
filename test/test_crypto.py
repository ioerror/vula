from unittest import TestCase, main


# fmt: off
class TestX25519(TestCase):

    # This fails on OpenBSD
    def test_x25519_keygen(self):
        import cryptography.hazmat.primitives.asymmetric.x25519
        from cryptography.hazmat.primitives.asymmetric.x25519 import (
            X25519PrivateKey,
        )

        keypair = X25519PrivateKey.generate()
        try:

            if (
                type(keypair)
                == cryptography.hazmat.backends.openssl.x25519._X25519PrivateKey  # noqa: E501
            ):
                self.assertIsInstance(
                    keypair,
                    cryptography.hazmat.backends.openssl.x25519._X25519PrivateKey,  # noqa: E501
                )
        except AttributeError:
            if (
                type(keypair)
                == cryptography.hazmat.bindings._rust.openssl.x25519.X25519PrivateKey  # noqa: E501
            ):
                self.assertIsInstance(
                    keypair,
                    cryptography.hazmat.bindings._rust.openssl.x25519.X25519PrivateKey,  # noqa: E501
                )


# fmt: on

if __name__ == '__main__':
    main()
