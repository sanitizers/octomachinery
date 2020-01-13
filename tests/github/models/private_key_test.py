"""Tests for GitHub private key class."""
# pylint: disable=redefined-outer-name
from datetime import date
from pathlib import Path
import random
import re

import pytest

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)
from jwt import decode as parse_jwt

from octomachinery.github.models.private_key import GitHubPrivateKey


@pytest.fixture
def rsa_public_key(rsa_private_key):
    """Extract a public key out of private one."""
    return rsa_private_key.public_key()


@pytest.fixture
def rsa_public_key_bytes(rsa_public_key) -> bytes:
    """Return a PKCS#1 formatted RSA public key encoded as PEM."""
    return rsa_public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.PKCS1,
    )


@pytest.fixture
def github_private_key(rsa_private_key_bytes: bytes) -> GitHubPrivateKey:
    """Construct a test instance of ``GitHubPrivateKey``."""
    return GitHubPrivateKey(rsa_private_key_bytes)


@pytest.fixture
def rsa_private_key_path(
        rsa_private_key_bytes: bytes,
        tmp_path_factory,
) -> Path:
    """Save the private key to disk as PEM file and provide its path."""
    tmp_dir = tmp_path_factory.mktemp('github_private_key')
    private_key_filename = (
        f'test-github-app.{date.today():%Y-%m-%d}'
        '.private-key.pem'
    )
    private_key_path = tmp_dir / private_key_filename
    private_key_path.write_bytes(rsa_private_key_bytes)
    return private_key_path


def test_github_private_key__from_file(
        github_private_key,
        rsa_private_key_path: Path,
):
    """Test that GitHubPrivateKey from file and bytes are the same."""
    key_from_file = GitHubPrivateKey.from_file(rsa_private_key_path)
    assert key_from_file == github_private_key


def test_github_private_key____repr__(github_private_key):
    """Verify what repr protocol only exposes fingerprint."""
    repr_pattern = re.compile(
        r"^<GitHubPrivateKey\(b_raw_data=b'<SECRET>'\)\s"
        r'with\sSHA\-1\sfingerprint\s'
        r"'[a-f0-9]{2}(:[a-f0-9]{2}){19}'>$",
    )
    assert repr_pattern.match(repr(github_private_key))
    assert repr_pattern.match(f'{github_private_key!r}')


def test_github_private_key____str__(github_private_key):
    """Verify that the string protocol doesn't expose secrets."""
    escaped_private_key_repr = (
        repr(github_private_key).
        replace('(', r'\(').
        replace(')', r'\)')
    )
    exception_message = (
        "<class 'octomachinery.github.models.private_key.GitHubPrivateKey'> "
        'objects do not implement the string protocol '
        'for security reasons. '
        f'The repr of this instance is {escaped_private_key_repr!s}.'
    )
    with pytest.raises(TypeError, match=exception_message):
        str(github_private_key)
    with pytest.raises(TypeError, match=exception_message):
        f'{github_private_key!s}'  # pylint: disable=pointless-statement


def test_github_private_key__make_jwt_for(
        github_private_key: GitHubPrivateKey,
        rsa_public_key_bytes,
):
    """Verify that e2e encoding-decoding of the JWT works."""
    github_app_id = random.randint(0, 9999999)
    jwt_string = github_private_key.make_jwt_for(app_id=github_app_id)
    payload = parse_jwt(
        jwt_string.encode('utf-8'), rsa_public_key_bytes, algorithms='RS256',
    )
    assert payload['iss'] == github_app_id
    assert payload['exp'] - payload['iat'] == 60


def test_github_private_key__make_jwt_for__invalid_timeout(github_private_key):
    """Verify that time offset can't exceed 10 mins."""
    github_app_id = random.randint(0, 9999999)
    with pytest.raises(
            ValueError,
            match='The time offset must be less than 10 minutes',
    ):
        github_private_key.make_jwt_for(app_id=github_app_id, time_offset=601)
