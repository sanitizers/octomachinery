"""GitHub Action wrapper."""

import logging

import attr

# pylint: disable=relative-beyond-top-level
from ...app.action.config import GitHubActionConfig
# pylint: disable=relative-beyond-top-level
from ..api.app_client import GitHubApp
# pylint: disable=relative-beyond-top-level
from ..api.raw_client import RawGitHubAPI
# pylint: disable=relative-beyond-top-level
from ..api.tokens import GitHubOAuthToken
# pylint: disable=relative-beyond-top-level,import-error
from ..models.events import GidgetHubActionEvent


logger = logging.getLogger(__name__)


@attr.dataclass
class GitHubAction(GitHubApp):
    """GitHub Action API wrapper."""

    _metadata: GitHubActionConfig  # FIXME: _config?  # pylint: disable=fixme
    """A GitHub Action metadata from envronment vars."""

    @property
    def event(self):  # noqa: D401
        """Parsed GitHub Action event data."""
        return GidgetHubActionEvent.from_file(
            self._metadata.event_name,
            self._metadata.event_path,
        )

    @property
    def token(self):
        """Return GitHub Action access token."""
        return GitHubOAuthToken(self._metadata.token)

    @property
    def api_client(self):  # noqa: D401
        """The GitHub App client."""
        return RawGitHubAPI(
            token=self.token,
            session=self._http_session,
            user_agent=self._config.user_agent,
        )
