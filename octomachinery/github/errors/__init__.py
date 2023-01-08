"""Exceptions collection related to interactions with GitHub."""

from gidgethub import GitHubException

import attr

# pylint: disable=relative-beyond-top-level
from ..models.action_outcomes import ActionOutcome


class GitHubError(GitHubException):
    """Generic GitHub-related error."""


@attr.dataclass
class GitHubActionError(GitHubError):
    """Generic GitHub-related error."""

    _outcome: ActionOutcome

    def terminate_action(self):
        """Terminate current process using corresponding return code."""
        self._outcome.raise_it()
