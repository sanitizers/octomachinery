"""Utility helpers for App/Action installations."""

from base64 import b64decode
from http import HTTPStatus
from io import StringIO
from pathlib import Path
import typing

import gidgethub
import yaml

# pylint: disable=relative-beyond-top-level
from ...runtime.context import RUNTIME_CONTEXT


def _get_file_contents_from_fs(file_name: str) -> typing.Optional[str]:
    """Read file contents from file system checkout.

    This code path is synchronous.

    It doesn't matter much in GitHub Actions
    but can be refactored later.
    """
    config_path = (Path('.') / file_name)

    try:
        return config_path.read_text()
    except FileNotFoundError:
        return None


async def _get_file_contents_from_api(
        file_name: str,
        ref: typing.Optional[str],
) -> typing.Optional[str]:
    """Read file contents using GitHub API."""
    github_api = RUNTIME_CONTEXT.app_installation_client
    repo_slug = RUNTIME_CONTEXT.github_event.payload['repository']['full_name']

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

    return await _get_file_contents_from_api(file_path, ref)


async def get_installation_config(
        *,
        config_name: str = 'config.yml',
        ref: typing.Optional[str] = None,
) -> typing.Mapping[str, typing.Any]:
    """Get a config object from the current installation.

    Read from file system checkout in case of GitHub Action env.
    Grab it via GitHub API otherwise.

    Usage::

        >>> from octomachinery.app.runtime.installation_utils import (
        ...     get_installation_config
        ... )
        >>> await get_installation_config()
    """
    config_path = f'.github/{config_name}'

    config_content = await read_file_contents_from_repo(
        file_path=config_path,
        ref=ref,
    )

    if config_content is None:
        return {}

    return yaml.load(StringIO(config_content))
