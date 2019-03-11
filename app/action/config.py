"""GitHub Action environment and metadata representation."""

import json
from pathlib import Path
from uuid import uuid4

import environ
from gidgethub.sansio import Event

# pylint: disable=relative-beyond-top-level
from ...github.models.utils import SuperSecretStr


@environ.config  # pylint: disable=too-few-public-methods
class GitHubActionConfig:
    """GitHub Action config."""

    workflow = environ.var(
        None, name='GITHUB_WORKFLOW',
    )
    action = environ.var(
        None, name='GITHUB_ACTION',
    )
    actor = environ.var(
        None, name='GITHUB_ACTOR',
    )
    repository = environ.var(
        None, name='GITHUB_REPOSITORY',
    )
    event_name = environ.var(
        None, name='GITHUB_EVENT_NAME',
    )
    event_path = environ.var(
        None, converter=lambda p: p if p is None else Path(p),
        name='GITHUB_EVENT_PATH',
    )
    workspace = environ.var(
        None, name='GITHUB_WORKSPACE',
    )
    sha = environ.var(
        None, name='GITHUB_SHA',
    )
    ref = environ.var(
        None, name='GITHUB_REF',
    )
    token = environ.var(
        None, name='GITHUB_TOKEN',
        converter=lambda t: t if t is None else SuperSecretStr(t),
    )

    @property
    def event(self):  # noqa: D401
        """Return parsed event data."""
        try:
            # NOTE: This could be async but it probably doesn't matter
            # NOTE: since it's called just once during init and GitHub
            # NOTE: Action runtime only has one event to process
            # pylint: disable=no-member
            with self.event_path.open() as event_source:
                return Event(
                    json.load(event_source),
                    event=self.event_name,
                    delivery_id=uuid4(),
                )
        except TypeError:
            return None
