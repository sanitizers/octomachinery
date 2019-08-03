"""Actions processor test suite."""
# pylint: disable=redefined-outer-name

import json

import pytest

from octomachinery.app.action.config import GitHubActionConfig
from octomachinery.app.action.runner import run
from octomachinery.app.config import BotAppConfig
from octomachinery.app.runtime.config import RuntimeConfig
from octomachinery.app.server.config import WebServerConfig
from octomachinery.github.config.app import GitHubAppIntegrationConfig


@pytest.fixture
def event_file(tmp_path_factory):
    """Generate a sample JSON event file."""
    gh_event = (
        tmp_path_factory.mktemp('github-action-event') /
        'github-workflow-event.json'
    )
    with gh_event.open('w') as gh_event_file:
        json.dump(
            {
            },
            gh_event_file,
        )
    return gh_event


@pytest.fixture
def config(monkeypatch, event_file):
    """Create a dummy GitHub Action config."""
    monkeypatch.setattr(
        'octomachinery.app.runtime.utils.detect_env_mode',
        lambda: 'action',
    )
    return BotAppConfig(
        github=GitHubAppIntegrationConfig(),
        action=GitHubActionConfig(
            workflow='Test Workflow',
            action='Test Action',
            actor='username-or-bot',
            repository='org/repo',
            event_name='check_run',
            event_path=str(event_file),  # '/github/workflow/event.json'
            workspace='/github/workspace',
            sha='e6d4abcb8a6cd989d41ee',
            ref='refs/heads/master',
            token='8sdfn12lifds8sdvh832n32f9jew',
        ),
        server=WebServerConfig(),
        runtime=RuntimeConfig(),
    )


def test_run(config):
    """Test an empty action processing run."""
    with pytest.raises(SystemExit, match=r'^0$'):
        run(config=config)
