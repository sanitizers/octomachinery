"""A very low-level GitHub API client."""

from typing import Any, Dict, Optional, Tuple

from aiohttp import ClientSession
from gidgethub.aiohttp import GitHubAPI

# pylint: disable=relative-beyond-top-level
from ...app.runtime.context import RUNTIME_CONTEXT
# pylint: disable=relative-beyond-top-level
from .tokens import GitHubToken, GitHubOAuthToken, GitHubJWTToken


class RawGitHubAPI(GitHubAPI):
    """A low-level GitHub API client with a pre-populated token."""

    def __init__(
            self,
            token: GitHubToken,
            *,
            session: Optional[ClientSession] = None,
            user_agent: Optional[str] = None,
            **kwargs: Any,
    ) -> None:
        """Initialize the GitHub client with token."""
        self._token = token
        kwargs.pop('oauth_token', None)
        kwargs.pop('jwt', None)
        super().__init__(
            requester=user_agent or RUNTIME_CONTEXT.config.github.user_agent,
            session=session or ClientSession(),
            **kwargs,
        )

    # pylint: disable=arguments-differ
    # pylint: disable=keyword-arg-before-vararg
    # pylint: disable=too-many-arguments
    async def _make_request(
            self, method: str, url: str, url_vars: Dict[str, str],
            data: Any, accept: str,
            jwt: Optional[str] = None,
            oauth_token: Optional[str] = None,
            *args: Any, **kwargs: Any,
    ) -> Tuple[bytes, Optional[str]]:
        kwargs.pop('oauth_token', None)
        kwargs.pop('jwt', None)
        if isinstance(self._token, GitHubOAuthToken):
            kwargs['oauth_token'] = str(self._token)
        if isinstance(self._token, GitHubJWTToken):
            kwargs['jwt'] = str(self._token)
        return await super()._make_request(
            method, url, url_vars,
            data, accept,
            *args, **kwargs,
        )
