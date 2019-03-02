"""GitHub token types definitions."""

import attr

# pylint: disable=relative-beyond-top-level
from ..models.utils import SecretStr


@attr.dataclass
class GitHubToken:  # pylint: disable=too-few-public-methods
    """Base class for GitHub tokens."""

    _token_value: SecretStr = attr.ib(
        lambda s: SecretStr(s) if s is not None else s,
    )

    def __str__(self):
        """Render the token as its string value."""
        return self._token_value


@attr.dataclass  # pylint: disable=too-few-public-methods
class GitHubOAuthToken(GitHubToken):
    r"""GitHub OAuth Token.

    It can represent either App Installation token or a personal one.

    Ref: https://developer.github.com\
         /apps/building-github-apps/authenticating-with-github-apps\
         /#authenticating-as-an-installation
    """


@attr.dataclass  # pylint: disable=too-few-public-methods
class GitHubJWTToken(GitHubToken):
    r"""GitHub JSON Web Token.

    It represents GitHub App token.

    Ref: https://developer.github.com\
         /apps/building-github-apps\
         /authenticating-with-github-apps/#authenticating-as-a-github-app
    """
