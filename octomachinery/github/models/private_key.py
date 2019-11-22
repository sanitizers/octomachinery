"""Private key container."""
from hashlib import sha1 as compute_sha1_hash
from pathlib import Path
from time import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from jwt import encode as compute_jwt


def extract_public_key_sha1_from_private_key(rsa_private_key):
    r"""Retrieve SHA-1 digest of the public key from the private key.

    :param rsa_private_key: private key object
    :type rsa_private_key: cryptography.hazmat.primitives.asymmetric.\
                           rsa.RSAPrivateKey

    :returns: colon-separated SHA-1 hash string
    :rtype: str
    """
    rsa_public_key = rsa_private_key.public_key()
    b_rsa_public_key = rsa_public_key.public_bytes(
        Encoding.DER,
        PublicFormat.SubjectPublicKeyInfo,
    )
    rsa_public_key_sha1_hash_digest = compute_sha1_hash(
        b_rsa_public_key,
    ).hexdigest()

    def emit_chunks(sequence, step):
        start_pos = 0
        seq_length = len(sequence)
        while start_pos < seq_length:
            end_pos = start_pos + step
            yield sequence[start_pos: end_pos]
            start_pos = end_pos

    return ':'.join(
        emit_chunks(rsa_public_key_sha1_hash_digest, 2),
    )


class GitHubPrivateKey:
    """Private key entity with a pre-calculated public key SHA-1.

    :param bytes b_raw_data: the contents of a PEM file
    """

    def __init__(self, b_raw_data: bytes):
        """Initialize GitHubPrivateKey instance."""
        self._rsa_private_key = load_pem_private_key(
            b_raw_data,
            password=None,
            backend=default_backend(),
        )
        self._col_separated_rsa_public_key_sha1_hash_digest = (
            extract_public_key_sha1_from_private_key(self._rsa_private_key)
        )

    @property
    def sha1_hash(self):
        """Colon-separated SHA1 hash string value of the public key.

        :returns: colon-separated SHA-1 hash string
        :rtype: str
        """
        return self._col_separated_rsa_public_key_sha1_hash_digest

    def __str__(self):
        """Avoid leaking private key contents via string protocol.

        :raises TypeError: always
        """
        raise TypeError(
            f'{type(self)} objects do not implement the string protocol '
            'for security reasons. '
            f'The repr of this instance is {self!r}.',
        )

    def __repr__(self):
        r"""Construct a GitHubPrivateKey object representation.

        :returns: GitHubPrivateKey object representation \
                  with a SHA-1 of the public key
        :rtype: str
        """
        return (
            "<GitHubPrivateKey(b_raw_data=b'<SECRET>') "
            f"with public key SHA-1 hash digest '{self.sha1_hash}>'"
        )

    def __eq__(self, other_private_key):
        r"""Compare equality of our private key with other.

        :returns: the result of comparison with another \
                  ``GitHubPrivateKey`` instance
        :rtype: bool
        """
        return self.matches_hash(other_private_key.sha1_hash)

    def matches_hash(self, other_hash):
        """Compare our public key SHA-1 with ``other_hash``.

        :returns: the result of own SHA-1 hash comparison with ``other_hash``
        :rtype: bool
        """
        return self.sha1_hash == other_hash

    @classmethod
    def from_file(cls, path):
        r"""Construct a ``GitHubPrivateKey`` instance.

        :returns: the ``GitHubPrivateKey`` instance \
                  constructed of the target file contents
        :rtype: GitHubPrivateKey
        """
        return cls(Path(path).expanduser().read_bytes())

    def make_jwt_for(self, *, app_id: int, time_offset: int = 60) -> str:
        r"""Generate app's JSON Web Token.

        :param int app_id: numeric ID of a GitHub App
        :param int time_offset: duration of the JWT's validity, in seconds, \
                                defaults to 60

        :returns: JWT string for a GitHub App valid for the given time
        :rtype: str

        :raises ValueError: if time_offset exceeds 600 seconds (10 minutes)
        """
        ten_min = 60 * 10
        if time_offset > ten_min:
            raise ValueError('The time offset must be less than 10 minutes')

        now = int(time())
        payload = {
            'iat': now,
            'exp': now + 60,
            'iss': app_id,
        }

        return compute_jwt(
            payload,
            key=self._rsa_private_key,
            algorithm='RS256',
        ).decode('utf-8')
