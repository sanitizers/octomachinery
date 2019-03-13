"""GitHub Action environment and metadata representation."""

from pathlib import Path

import environ

# pylint: disable=relative-beyond-top-level
from ...github.models.utils import SecretStr


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
        converter=lambda t: t if t is None else SecretStr(t),
    )
