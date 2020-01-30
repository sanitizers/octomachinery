"""GitHub Action wrapper."""

import logging

from aiohttp.client import ClientSession
import attr

# pylint: disable=relative-beyond-top-level
from ...app.action.config import GitHubActionConfig
# pylint: disable=relative-beyond-top-level
from ..api.raw_client import RawGitHubAPI
# pylint: disable=relative-beyond-top-level
from ..api.tokens import GitHubOAuthToken
# pylint: disable=relative-beyond-top-level,import-error
from ..models.events import GidgetHubActionEvent


logger = logging.getLogger(__name__)


@attr.dataclass
class GitHubAction:  # FIXME: should inherit GitHubApp?
    """GitHub Action API wrapper."""

    _metadata: GitHubActionConfig  # FIXME: _config?
    """A GitHub Action metadata from envronment vars."""
    _http_session: ClientSession
    """An externally created aiohttp client session."""
    _user_agent: str
    """A User-Agent string to use in HTTP requests to the GitHub API."""

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
            user_agent=self._user_agent,
        )
