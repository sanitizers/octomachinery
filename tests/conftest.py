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
    stands in for the ``event_loop`` fixture that ``pytest-asyncio`` used
    to provide, which is no longer installed at all.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        _shut_down_event_loop(loop)
        asyncio.set_event_loop(None)
        loop.close()


def _shut_down_event_loop(loop):
    """Drain the leftovers of the event loop before closing it.

    Closing a loop right away leaves the fire-and-forget tasks and the
    transports that only complete closing on the next iteration hanging
    around. The garbage collector then emits a ``ResourceWarning`` for
    each of them, which ``pytest`` turns into an error attributed to
    whatever test happens to be running at that moment.
    """
    leftover_tasks = [
        task for task in asyncio.all_tasks(loop) if not task.done()
    ]
    for task in leftover_tasks:
        task.cancel()
    if leftover_tasks:
        loop.run_until_complete(
            asyncio.gather(*leftover_tasks, return_exceptions=True),
        )

    loop.run_until_complete(loop.shutdown_asyncgens())

    # NOTE: `transport.close()` only schedules the connection loss
    # NOTE: callback, so the loop needs one more iteration to invoke it.
    loop.run_until_complete(asyncio.sleep(0))


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
