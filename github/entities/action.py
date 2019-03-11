"""GitHub Action wrapper."""

import logging

import attr

# pylint: disable=relative-beyond-top-level
from ...app.action.config import GitHubActionConfig
# pylint: disable=relative-beyond-top-level
from ..api.client import GitHubAPIClient
# pylint: disable=relative-beyond-top-level
from ..api.tokens import GitHubOAuthToken


logger = logging.getLogger(__name__)


@attr.dataclass
class GitHubAction:
    """GitHub Action API wrapper."""

    _metadata: GitHubActionConfig
    """A GitHub Action metadata from envronment vars."""

    @property
    def event(self):
        """Return GitHub Action event."""
        return self._metadata.event

    @property
    def token(self):
        """Return GitHub Action access token."""
        return GitHubOAuthToken(self._metadata.token)

    @property
    def github_installation_client(self):  # noqa: D401
        """The GitHub App client with an async CM interface."""
        return GitHubAPIClient(self.token)
