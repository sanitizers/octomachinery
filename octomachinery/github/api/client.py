"""A low-level GitHub API client."""

from contextlib import AbstractAsyncContextManager
import types
import typing

import aiohttp
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
    _external_session: typing.Optional[aiohttp.ClientSession] = (
        attr.ib(default=None)
    )
    """A session created externally."""
    _current_session: aiohttp.ClientSession = attr.ib(init=False, default=None)
    """A session created per CM if there's no external one."""
    _api_client: RawGitHubAPI = attr.ib(init=False, default=None)
    """A Gidgethub client for GitHub API."""

    def __attrs_post_init__(self):
        """Gidgethub API client instance initializer."""
        try:
            self._api_client = self.get_github_api_client(
                session=self._open_session(),
            )
        except (AttributeError, TypeError):
            pass

    def get_github_api_client(
            self,
            *,
            session: typing.Optional[aiohttp.ClientSession] = None,
    ):
        """Gidgethub API client instance."""
        extra_kwargs = {'session': session} if session is not None else {}

        return RawGitHubAPI(
            token=self._github_token,
            user_agent=self._user_agent,
            **extra_kwargs,
        )

    @property
    def is_initialized(self):
        """Return GitHub token presence."""
        return self._github_token is not None

    def _open_session(self) -> aiohttp.ClientSession:
        """Return a session to use with GitHub API."""
        assert self._current_session is None
        self._current_session = (
            aiohttp.ClientSession() if self._external_session is None
            else self._external_session
        )
        return self._current_session

    async def _close_session(self) -> None:
        """Free up the current session."""
        assert self._current_session is not None
        if self._external_session is None:
            await self._current_session.close()
        self._current_session = None

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
        await self._close_session()
