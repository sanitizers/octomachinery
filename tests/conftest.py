"""Shared fixtures for tests."""
import asyncio

import pytest

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.serialization import (
    Encoding, NoEncryption, PrivateFormat,
)


@pytest.fixture
def current_event_loop():
    """Provide a fresh asyncio event loop set as the current one.

    ``anyio < 2`` runs async tests and fixtures in the loop returned by
    ``asyncio.get_event_loop()`` so one must be set explicitly. This
    replaces the ``event_loop`` fixture removed in ``pytest-asyncio`` 1.0.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        asyncio.set_event_loop(None)
        loop.close()


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
