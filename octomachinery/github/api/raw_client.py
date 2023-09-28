"""A very low-level GitHub API client."""

from asyncio import iscoroutinefunction
from typing import Any, Dict, Optional, Tuple, Union

from gidgethub.abc import JSON_CONTENT_TYPE
from gidgethub.aiohttp import GitHubAPI

# pylint: disable=relative-beyond-top-level
from .tokens import GitHubJWTToken, GitHubOAuthToken, GitHubToken
from .utils import accept_preview_version, mark_uninitialized_in_repr


@mark_uninitialized_in_repr
class RawGitHubAPI(GitHubAPI):
    """A low-level GitHub API client with a pre-populated token."""

    def __init__(
            self,
            token: GitHubToken,
            *,
            user_agent: Optional[str] = None,
            **kwargs: Any,
    ) -> None:
        """Initialize the GitHub client with token."""
        self._token = token
        kwargs.pop('oauth_token', None)
        kwargs.pop('jwt', None)
        super().__init__(
            requester=user_agent,
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
            data: Any, accept: Union[str, None] = None,
            jwt: Optional[str] = None,
            oauth_token: Optional[str] = None,
            content_type: str = JSON_CONTENT_TYPE,
            extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[bytes, Optional[str]]:
        token = self._token
        if iscoroutinefunction(token):
            token = await token()
        if isinstance(token, GitHubOAuthToken):
            oauth_token = str(token)
            jwt = None
        if isinstance(token, GitHubJWTToken):
            jwt = str(token)
            oauth_token = None
        optional_kwargs = {
            # NOTE: GidgetHub v5.3.0 introduced a new `extra_headers` argument
            # NOTE: in this private method and the public ones. Its default
            # NOTE: value is `None` in all cases so the only case when it's set
            # NOTE: is when the end-users call corresponding methods with it.
            # NOTE: And that would only be the case with modern versions of
            # NOTE: GidgetHub. Here, we rely on this side effect to only pass
            # NOTE: this value down the stack when the chances that GidgetHub
            # NOTE: is modern enough are close to 100%.
            'extra_headers': extra_headers,
        } if extra_headers is not None else {}
        return await super()._make_request(
            method=method,
            url=url,
            url_vars=url_vars,
            data=data,
            accept=accept,
            oauth_token=oauth_token,
            jwt=jwt,
            content_type=content_type,
            **optional_kwargs,
        )

    getitem = accept_preview_version(GitHubAPI.getitem)
    getiter = accept_preview_version(GitHubAPI.getiter)
    post = accept_preview_version(GitHubAPI.post)
    patch = accept_preview_version(GitHubAPI.patch)
    put = accept_preview_version(GitHubAPI.put)
    delete = accept_preview_version(GitHubAPI.delete)
