"""Shared fixtures for tests."""

import pytest

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.serialization import (
    Encoding, NoEncryption, PrivateFormat,
)


@pytest.fixture
def anyio_backend():
    """Pin the async test backend to asyncio.

    ``aiohttp`` only supports asyncio. The ``anyio`` pytest plugin's
    own ``anyio_backend`` fixture parametrizes over every backend
    ``anyio`` knows about, trio included, which makes no sense here.
    """
    return 'asyncio'


@pytest.fixture
def rsa_private_key():
    """Generate an RSA private key."""
    return generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend(),
    )


@pytest.fixture
def rsa_private_key_bytes(rsa_private_key) -> bytes:
    r"""Generate an unencrypted PKCS#1 formatted RSA private key.

    Encoded as PEM-bytes.

    This is what the GitHub-downloaded PEM files contain.

    Ref: https://developer.github.com/apps/building-github-apps/\
         authenticating-with-github-apps/
    """
    return rsa_private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,  # A.K.A. PKCS#1
        encryption_algorithm=NoEncryption(),
    )
