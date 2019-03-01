"""A low-level GitHub API client."""

from contextlib import AbstractAsyncContextManager
import types
import typing

import aiohttp
import attr
import gidgethub.aiohttp

# pylint: disable=relative-beyond-top-level
from ...app.runtime.context import RUNTIME_CONTEXT
from .installation_client import GitHubAppInstallationAPIClient


@attr.dataclass
class GitHubAPIClient(AbstractAsyncContextManager):
    """A client to the GitHub API with an asynchronous CM support."""

    _external_session: typing.Optional[aiohttp.ClientSession] = (
        attr.ib(default=None)
    )
    """A session created externally."""
    _current_session: aiohttp.ClientSession = attr.ib(init=False, default=None)
    """A session created per CM if there's no external one."""

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

    async def __aenter__(self) -> gidgethub.aiohttp.GitHubAPI:
        """Return a GitHub API wrapper."""
        self._open_session()
        gh_api_client = gidgethub.aiohttp.GitHubAPI(
            self._current_session,
            RUNTIME_CONTEXT.config.github.user_agent,
        )
        async with GitHubAppInstallationAPIClient(
                self._current_session,
        ) as gh_api_install_client:
            RUNTIME_CONTEXT.app_installation_client = gh_api_install_client
        return gh_api_client

    async def __aexit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            exc_val: typing.Optional[BaseException],
            exc_tb: typing.Optional[types.TracebackType],
    ) -> typing.Optional[bool]:
        """Close the current session resource."""
        await self._close_session()
