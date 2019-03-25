"""A very low-level GitHub API client."""

from typing import Any, Dict, Mapping, Optional, Tuple

from aiohttp import ClientSession
from gidgethub.aiohttp import GitHubAPI

# pylint: disable=relative-beyond-top-level
from .tokens import GitHubToken, GitHubOAuthToken, GitHubJWTToken
from .utils import accept_preview_version, mark_uninitialized_in_repr


@mark_uninitialized_in_repr
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
            requester=user_agent,
            session=session,
            **kwargs,
        )

    @property
    def is_initialized(self):
        """Return GitHub token presence."""
        return self._token is not None

    def __repr__(self):
        """Render a class instance representation."""
        cls_name = self.__class__.__name__
        init_args = (
            f'token={self._token!r}, '
            f'session={self._session!r}, '
            f'user_agent={self.requester!r}'
        )
        return f'{cls_name}({init_args})'

    # pylint: disable=arguments-differ
    # pylint: disable=keyword-arg-before-vararg
    # pylint: disable=too-many-arguments
    async def _make_request(
            self, method: str, url: str, url_vars: Dict[str, str],
            data: Any, accept: str = None,
            jwt: Optional[str] = None,
            oauth_token: Optional[str] = None,
    ) -> Tuple[bytes, Optional[str]]:
        if isinstance(self._token, GitHubOAuthToken):
            oauth_token = str(self._token)
            jwt = None
        if isinstance(self._token, GitHubJWTToken):
            jwt = str(self._token)
            oauth_token = None
        return await super()._make_request(
            method=method,
            url=url,
            url_vars=url_vars,
            data=data,
            accept=accept,
            oauth_token=oauth_token,
            jwt=jwt,
        )

    async def _request(
            self,
            method: str,
            url: str,
            headers: Mapping[str, str],
            body: bytes = b'',
    ) -> Tuple[int, Mapping[str, str], bytes]:
        has_persistent_session = self._session is not None

        if has_persistent_session:
            return await super()._request(
                method, url,
                headers, body,
            )

        try:
            self._session = ClientSession()

            async with self._session:
                return await super()._request(
                    method, url,
                    headers, body,
                )
        finally:
            self._session = None

    getitem = accept_preview_version(GitHubAPI.getitem)
    getiter = accept_preview_version(GitHubAPI.getiter)
    post = accept_preview_version(GitHubAPI.post)
    patch = accept_preview_version(GitHubAPI.patch)
    put = accept_preview_version(GitHubAPI.put)
    delete = accept_preview_version(GitHubAPI.delete)
