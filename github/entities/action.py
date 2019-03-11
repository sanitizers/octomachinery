"""GitHub Action wrapper."""

import json
import logging
from uuid import uuid4

import attr
from gidgethub.sansio import Event

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
    def event(self):  # noqa: D401
        """Parsed GitHub Action event data."""
        try:
            # NOTE: This could be async but it probably doesn't matter
            # NOTE: since it's called just once during init and GitHub
            # NOTE: Action runtime only has one event to process
            # pylint: disable=no-member
            with self._metadata.event_path.open() as event_source:
                return Event(
                    json.load(event_source),
                    event=self._metadata.event_name,
                    delivery_id=uuid4(),
                )
        except TypeError:
            return None

    @property
    def token(self):
        """Return GitHub Action access token."""
        return GitHubOAuthToken(self._metadata.token)

    @property
    def github_installation_client(self):  # noqa: D401
        """The GitHub App client with an async CM interface."""
        return GitHubAPIClient(self.token)
