"""A low-level GitHub API client."""

from contextlib import AbstractAsyncContextManager
import types
import typing

from aiohttp.client import ClientSession
import attr

# pylint: disable=relative-beyond-top-level
from .raw_client import RawGitHubAPI
# pylint: disable=relative-beyond-top-level
from .tokens import GitHubToken
# pylint: disable=relative-beyond-top-level
from .utils import mark_uninitialized_in_repr


@mark_uninitialized_in_repr
@attr.dataclass
class GitHubAPIClient(AbstractAsyncContextManager):
    """A client to the GitHub API with an asynchronous CM support."""

    _github_token: GitHubToken
    _user_agent: str
    """A User-Agent string to use in HTTP requests to the GitHub API."""
    _session: ClientSession
    """A session created externally."""
    _api_client: RawGitHubAPI = attr.ib(init=False, default=None)
    """A Gidgethub client for GitHub API."""

    def __attrs_post_init__(self):
        """Gidgethub API client instance initializer."""
        try:
            self._api_client = self.get_github_api_client()
        except (AttributeError, TypeError):
            pass

    def get_github_api_client(self) -> RawGitHubAPI:
        """Gidgethub API client instance."""
        return RawGitHubAPI(
            token=self._github_token,
            session=self._session,
            user_agent=self._user_agent,
        )

    @property
    def is_initialized(self):
        """Return GitHub token presence."""
        return self._github_token is not None

    async def __aenter__(self) -> RawGitHubAPI:
        """Return a GitHub API wrapper."""
        return self._api_client

    async def __aexit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            exc_val: typing.Optional[BaseException],
            exc_tb: typing.Optional[types.TracebackType],
    ) -> typing.Optional[bool]:
        """Close the current session resource."""
