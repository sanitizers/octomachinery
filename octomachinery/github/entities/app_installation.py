"""GitHub App Installation wrapper."""

from __future__ import annotations

import logging
import typing

import aiohttp
import attr

# pylint: disable=relative-beyond-top-level
from ..api.client import GitHubAPIClient
# pylint: disable=relative-beyond-top-level
from ..api.raw_client import RawGitHubAPI
# pylint: disable=relative-beyond-top-level
from ..api.tokens import GitHubOAuthToken
# pylint: disable=relative-beyond-top-level
from ..models import (
    GitHubAppInstallation as GitHubAppInstallationModel,
    GitHubInstallationAccessToken,
)


if typing.TYPE_CHECKING:
    from ..api.app_client import GitHubApp


logger = logging.getLogger(__name__)


@attr.dataclass
class GitHubAppInstallation:
    """GitHub App Installation API wrapper."""

    _metadata: GitHubAppInstallationModel
    """A GitHub Installation metadata from GitHub webhook."""
    _github_app: GitHubApp
    """A GitHub App the Installation is associated with."""
    _token: GitHubInstallationAccessToken = attr.ib(init=False, default=None)
    """A GitHub Installation token for GitHub API."""

    @property
    def token(self):
        """Return GitHub App Installation access token."""
        try:
            if self._token.expired:
                return None

            return GitHubOAuthToken(self._token.token)
        except TypeError:
            return None

    async def retrieve_access_token(self):
        """Retrieve installation access token from GitHub API."""
        async with self._github_app.github_app_client as gh_api:
            self._token = GitHubInstallationAccessToken(**(await gh_api.post(
                self._metadata.access_tokens_url,
                data=b'',
                accept='application/vnd.github.machine-man-preview+json',
            )))
        return self._token

    def get_github_api_client(
            self,
            *,
            session: typing.Optional[aiohttp.ClientSession] = None,
    ):
        """Gidgethub API client instance."""
        extra_kwargs = {'session': session} if session is not None else {}

        return RawGitHubAPI(
            token=self.token,
            # pylint: disable=protected-access
            user_agent=self._github_app._config.user_agent,
            **extra_kwargs,
        )

    @property
    def github_installation_client(self):  # noqa: D401
        """The GitHub App client with an async CM interface."""
        return GitHubAPIClient(
            github_token=self.token,
            # pylint: disable=protected-access
            user_agent=self._github_app._config.user_agent,
        )
