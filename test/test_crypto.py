from unittest import TestCase, main


class TestX25519(TestCase):

    # This fails on OpenBSD
    def test_x25519_keygen(self):
        import cryptography.hazmat.primitives.asymmetric.x25519
        from cryptography.hazmat.primitives.asymmetric.x25519 import (
            X25519PrivateKey,
        )

        keypair = X25519PrivateKey.generate()
        self.assertIsInstance(
            keypair,
            cryptography.hazmat.backends.openssl.x25519._X25519PrivateKey,
        )


if __name__ == '__main__':
    main()
