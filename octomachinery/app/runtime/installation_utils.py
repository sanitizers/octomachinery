"""Utility helpers for App/Action installations."""

import re
import typing
from base64 import b64decode
from http import HTTPStatus
from io import StringIO
from pathlib import Path

import gidgethub

import yaml

# pylint: disable=relative-beyond-top-level
from ...runtime.context import RUNTIME_CONTEXT


_EXTENDS_REGEX = re.compile(
    r'(?:(?P<owner>[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38})/)?'
    r'(?P<repo>[-.\w]+)'
    r'(?::(?P<path>[-./\w]+\.ya?ml))?',
    flags=re.ASCII | re.IGNORECASE,
)
"""The Probot-compatible ``[owner/]repo[:path.yml]`` ``_extends`` value."""


def _get_file_contents_from_fs(file_name: str) -> typing.Optional[str]:
    """Read file contents from file system checkout.

    This code path is synchronous.

    It doesn't matter much in GitHub Actions
    but can be refactored later.
    """
    config_path = Path('.') / file_name

    try:
        return config_path.read_text()
    except FileNotFoundError:
        return None


def _get_current_repo_slug() -> str:
    """Get the ``owner/repo`` slug of the event repository."""
    return RUNTIME_CONTEXT.github_event.payload['repository']['full_name']


async def _get_file_contents_from_api(
        file_name: str,
        ref: typing.Optional[str],
        repo_slug: str,
) -> typing.Optional[str]:
    """Read file contents using GitHub API."""
    github_api = RUNTIME_CONTEXT.app_installation_client

    api_query_params = f'?ref={ref}' if ref else ''
    try:
        config_response = await github_api.getitem(
            f'/repos/{repo_slug}/contents'
            f'/{file_name}{api_query_params}',
        )
    except gidgethub.BadRequest as http_bad_req:
        if http_bad_req.status_code == HTTPStatus.NOT_FOUND:
            return None

        raise

    config_file_found = (
        config_response.get('encoding') == 'base64' and
        'content' in config_response
    )
    if not config_file_found:
        return None

    return b64decode(config_response['content']).decode()


async def read_file_contents_from_repo(
        *,
        file_path: str,
        ref: typing.Optional[str] = None,
) -> typing.Optional[str]:
    """Get a config object from the current installation.

    Read from file system checkout in case of GitHub Action env.
    Grab it via GitHub API otherwise.

    Usage::

        >>> from octomachinery.app.runtime.installation_utils import (
        ...     read_file_contents_from_repo
        ... )
        >>> await read_file_contents_from_repo(
        ...     '/file/path.txt',
        ...     ref='bdeaf38',
        ... )
    """
    if RUNTIME_CONTEXT.IS_GITHUB_ACTION and ref is None:
        return _get_file_contents_from_fs(file_path)

    return await _get_file_contents_from_api(
        file_path, ref, _get_current_repo_slug(),
    )


def _parse_config(
        config_content: typing.Optional[str],
        config_location: str,
) -> typing.Optional[typing.Dict[str, typing.Any]]:
    """Load a config mapping from YAML unless the file is missing."""
    if config_content is None:
        return None

    config = yaml.load(StringIO(config_content), Loader=yaml.SafeLoader)
    if config is None:  # the file is empty
        return {}

    if not isinstance(config, dict):
        raise ValueError(f'The config in {config_location} is not a mapping')

    return config


def _resolve_extends(
        extends: typing.Any,
        config_location: str,
        *,
        default_owner: str,
        default_path: str,
) -> typing.Tuple[str, str]:
    """Get the repository slug and the path of an extended config."""
    extends_match = (
        isinstance(extends, str) and _EXTENDS_REGEX.fullmatch(extends)
    )
    if not extends_match:
        raise ValueError(
            f'Invalid `_extends` value {extends!r} in {config_location}',
        )

    owner, repo, path = extends_match.group('owner', 'repo', 'path')
    return f'{owner or default_owner}/{repo}', path or default_path


async def get_installation_config(
        *,
        config_name: str = 'config.yml',
        ref: typing.Optional[str] = None,
) -> typing.Mapping[str, typing.Any]:
    """Get a config object from the current installation.

    Read from file system checkout in case of GitHub Action env.
    Grab it via GitHub API otherwise.

    The lookup is compatible with Probot. When the repository has no
    such config file, the same path in the ``.github`` repository of
    its owner is used instead. A config can inherit the top-level keys
    of another one by referring to it via the ``_extends`` key, as
    ``repo``, ``owner/repo`` or ``[owner/]repo:path/to/config.yml``.
    The ``ref`` only applies to the event repository.

    Usage::

        >>> from octomachinery.app.runtime.installation_utils import (
        ...     get_installation_config
        ... )
        >>> await get_installation_config()
    """
    config_path = f'.github/{config_name}'

    config = _parse_config(
        await read_file_contents_from_repo(file_path=config_path, ref=ref),
        config_path,
    )
    if config is not None and '_extends' not in config:
        # NOTE: GitHub Actions read the local checkout, so they don't
        # NOTE: depend on the repository being in the event payload.
        return config

    repo_owner, _, repo_name = _get_current_repo_slug().partition('/')
    if config is None and repo_name != '.github':
        repo_name = '.github'
        config = _parse_config(
            await _get_file_contents_from_api(
                config_path, None, f'{repo_owner}/{repo_name}',
            ),
            f'{repo_owner}/{repo_name}:{config_path}',
        )

    configs = []
    config_location = f'{repo_owner}/{repo_name}:{config_path}'
    loaded_config_locations = set()
    while config is not None:
        configs.append(config)
        loaded_config_locations.add(config_location)

        extends = config.pop('_extends', None)
        if not extends:
            break

        extended_repo_slug, extended_path = _resolve_extends(
            extends,
            config_location,
            default_owner=repo_owner,
            default_path=config_path,
        )
        extended_location = f'{extended_repo_slug}:{extended_path}'
        if extended_location in loaded_config_locations:
            raise ValueError(
                f'Recursive `_extends` value {extends!r} in {config_location}',
            )

        config_location = extended_location
        config = _parse_config(
            await _get_file_contents_from_api(
                extended_path, None, extended_repo_slug,
            ),
            config_location,
        )

    # A config overrides the top-level keys of the ones it extends:
    return {
        config_key: config_value
        for config in reversed(configs)
        for config_key, config_value in config.items()
    }
