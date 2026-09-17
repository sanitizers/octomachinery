"""Shared fixtures for tests."""

import asyncio
from typing import Iterator

import pytest

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey, generate_private_key,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding, NoEncryption, PrivateFormat,
)


@pytest.fixture
def rsa_private_key() -> RSAPrivateKey:
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


@pytest.fixture(autouse=True)
def _current_event_loop() -> Iterator[None]:
    """Keep a current event loop set for the duration of each test.

    ``anyio`` v1 deliberately grabs the current event loop through
    :func:`asyncio.get_event_loop` rather than :func:`asyncio.run` so
    that one loop is shared by the separate ``run()`` calls its pytest
    plugin makes for fixture set-up, the test itself and tear-down.
    Since Python 3.10, that call emits a :class:`DeprecationWarning`
    when no loop has been set -- and ``pytest.ini`` turns warnings into
    errors.

    Drop this fixture once the ``anyio < 2`` runtime pin is lifted.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield
    finally:
        asyncio.set_event_loop(None)
        loop.close()
