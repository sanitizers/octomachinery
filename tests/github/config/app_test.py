"""Tests for the GitHub App config."""

from aiohttp.client import ClientSession

import pytest
from unittest import mock  # pylint: disable=wrong-import-order

import environ

from octomachinery.app.action.config import GitHubActionConfig
from octomachinery.github.api.app_client import GitHubApp
from octomachinery.github.config.app import GitHubAppIntegrationConfig
from octomachinery.github.entities.action import GitHubAction
from octomachinery.github.entities.app_installation import (
    GitHubAppInstallation,
)
from octomachinery.github.models import (
    GitHubAppInstallation as GitHubAppInstallationModel,
)


GHE_API_URL = 'https://github.example.com/api/v3'


@pytest.fixture(autouse=True)
def _action_env_mode(monkeypatch):
    """Skip the mandatory GitHub App credentials validation."""
    monkeypatch.setattr(
        'octomachinery.app.runtime.utils.detect_env_mode',
        lambda: 'action',
    )


@pytest.fixture
def ghe_app_config(rsa_private_key_bytes):
    """Create a GitHub App config pointing at GitHub Enterprise."""
    return environ.to_config(
        GitHubAppIntegrationConfig,
        environ={
            'GITHUB_APP_IDENTIFIER': '12345',
            'GITHUB_PRIVATE_KEY': rsa_private_key_bytes.decode(),
            'GHE_HOST': 'github.example.com',
        },
    )


@pytest.mark.parametrize(
    ('env_vars', 'expected_api_base_url'),
    (
        pytest.param({}, 'https://api.github.com', id='github.com'),
        pytest.param(
            {'GHE_HOST': ''}, 'https://api.github.com',
            id='empty-GHE_HOST',
        ),
        pytest.param(
            {'GHE_PROTOCOL': 'http'}, 'https://api.github.com',
            id='GHE_PROTOCOL-without-GHE_HOST',
        ),
        pytest.param(
            {'GHE_HOST': 'github.example.com'}, GHE_API_URL,
            id='GHE_HOST',
        ),
        pytest.param(
            {'GHE_HOST': 'github.example.com', 'GHE_PROTOCOL': 'http'},
            'http://github.example.com/api/v3',
            id='GHE_HOST-and-GHE_PROTOCOL',
        ),
    ),
)
def test_api_base_url(env_vars, expected_api_base_url):
    """Check that GHE env vars define the GitHub API root URL."""
    config = environ.to_config(GitHubAppIntegrationConfig, environ=env_vars)
    assert config.api_base_url == expected_api_base_url


def test_app_api_clients_use_api_base_url(ghe_app_config):
    """Check that App and Installation clients hit the configured host."""
    github_app = GitHubApp(ghe_app_config, mock.Mock(spec=ClientSession))
    installation = GitHubAppInstallation(
        mock.Mock(spec=GitHubAppInstallationModel),
        github_app,
    )

    assert github_app.api_client.base_url == GHE_API_URL
    assert installation.api_client.base_url == GHE_API_URL


@pytest.mark.parametrize(
    ('action_env_vars', 'expected_api_base_url'),
    (
        pytest.param({}, GHE_API_URL, id='GHE_HOST'),
        pytest.param(
            {'GITHUB_API_URL': 'https://ghes.example.com/api/v3'},
            'https://ghes.example.com/api/v3',
            id='GITHUB_API_URL',
        ),
    ),
)
def test_action_api_client_base_url(
        ghe_app_config, action_env_vars, expected_api_base_url,
):
    """Check that Action client prefers the runner-provided API URL."""
    github_action = GitHubAction(
        ghe_app_config,
        mock.Mock(spec=ClientSession),
        metadata=environ.to_config(
            GitHubActionConfig,
            environ={'GITHUB_TOKEN': 'token', **action_env_vars},
        ),
    )

    assert github_action.api_client.base_url == expected_api_base_url
