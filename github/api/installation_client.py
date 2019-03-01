"""GitHub App Installation API Client."""

from contextlib import AbstractAsyncContextManager
import logging
import types
import typing

from aiohttp import ClientSession
import attr
from gidgethub.aiohttp import GitHubAPI

# pylint: disable=relative-beyond-top-level
from ...app.runtime.context import RUNTIME_CONTEXT


logger = logging.getLogger(__name__)


@attr.dataclass
class GitHubAppInstallationAPIClient(AbstractAsyncContextManager):
    """An install client to the GitHub API with an async CM."""

    _external_session: typing.Optional[ClientSession] = (
        attr.ib(default=None)
    )
    """A session created externally."""
    _current_session: ClientSession = attr.ib(init=False, default=None)
    """A session created per CM if there's no external one."""
    _api_client: GitHubAPI = attr.ib(init=False, default=None)
    """A Gidgethub client for GitHub API."""

    def __attrs_post_init__(self):
        """Gidgethub instance initializer."""
        try:
            self._api_client = GitHubAPI(
                self._open_session(),
                RUNTIME_CONTEXT.config.github.user_agent,
                oauth_token=RUNTIME_CONTEXT.app_installation['access'].token,
            )
        except AttributeError:
            pass

    def _open_session(self) -> ClientSession:
        """Return a session to use with GitHub API."""
        assert self._current_session is None
        self._current_session = (
            ClientSession() if self._external_session is None
            else self._external_session
        )
        return self._current_session

    async def __aenter__(self) -> GitHubAPI:
        """Return a GitHub API wrapper."""
        return self._api_client

    async def __aexit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            exc_val: typing.Optional[BaseException],
            exc_tb: typing.Optional[types.TracebackType],
    ) -> typing.Optional[bool]:
        """Do nothing."""
