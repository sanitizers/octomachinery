"""GitHub Action wrapper."""

from __future__ import annotations

import logging
import typing

import attr

# pylint: disable=relative-beyond-top-level
from ..api.app_client import GitHubApp
# pylint: disable=relative-beyond-top-level
from ..api.raw_client import RawGitHubAPI
# pylint: disable=relative-beyond-top-level
from ..api.tokens import GitHubOAuthToken
# pylint: disable=relative-beyond-top-level,import-error
from ..models.events import GidgetHubActionEvent


if typing.TYPE_CHECKING:
    # pylint: disable=relative-beyond-top-level
    from ...app.action.config import GitHubActionConfig
    # pylint: disable=relative-beyond-top-level
    from ..models.events import GitHubEvent


logger = logging.getLogger(__name__)


@attr.dataclass
class GitHubAction(GitHubApp):
    """GitHub Action API wrapper."""

    _metadata: GitHubActionConfig = attr.ib(default=None)
    """A GitHub Action metadata from envronment vars."""

    @_metadata.validator
    def _verify_metadata_is_set(self, attribute, value) -> None:
        if value is None:
            raise ValueError(f'{attribute} must be set.')

    @property
    def event(self) -> GitHubEvent:  # noqa: D401
        """Parsed GitHub Action event data."""
        return GidgetHubActionEvent.from_file(
            self._metadata.event_name,  # pylint: disable=no-member
            self._metadata.event_path,  # pylint: disable=no-member
        )

    @property
    def token(self) -> GitHubOAuthToken:
        """Return GitHub Action access token."""
        return GitHubOAuthToken(
            self._metadata.token,  # pylint: disable=no-member
        )

    @property
    def api_client(self) -> RawGitHubAPI:  # noqa: D401
        """The GitHub App client."""
        return RawGitHubAPI(
            token=self.token,
            session=self._http_session,
            user_agent=self._config.user_agent,
        )
