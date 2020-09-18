"""Actions processor test suite."""
# pylint: disable=redefined-outer-name

import json

import pytest

from octomachinery.app.action.config import GitHubActionConfig
from octomachinery.app.action.runner import run
from octomachinery.app.config import BotAppConfig
from octomachinery.app.routing import process_event
from octomachinery.app.routing import process_event_actions
from octomachinery.app.runtime.config import RuntimeConfig
from octomachinery.app.server.config import WebServerConfig
from octomachinery.github.config.app import GitHubAppIntegrationConfig
from octomachinery.github.errors import GitHubActionError
from octomachinery.github.models.action_outcomes import ActionNeutral


@process_event('unmatched_event', action='happened')
async def unmatched_event_happened(action):  # pylint: disable=unused-argument
    """Handle an unmached event."""


@process_event('check_run', action='created')
async def check_run_created(action):  # pylint: disable=unused-argument
    """Handle a check_run event."""
    raise RuntimeError('Emulate an unhandled error in the handler')


@process_event_actions('neutral_event', {'qwerty'})
async def neutral_event_qwerty(action):  # pylint: disable=unused-argument
    """Handle a neutral_event."""
    raise GitHubActionError(ActionNeutral('Neutral outcome'))


@process_event_actions('neutral_event')
async def neutral_event_dummy(action):  # pylint: disable=unused-argument
    """Handle any neutral event."""


@pytest.fixture
def event_file(tmp_path_factory, request):
    """Generate a sample JSON event file."""
    gh_event = (
        tmp_path_factory.mktemp('github-action-event') /
        'github-workflow-event.json'
    )
    with gh_event.open('w') as gh_event_file:
        json.dump(
            {
                'action': request.param,  # 'created',
            },
            gh_event_file,
        )
    return gh_event


@pytest.fixture
def config(monkeypatch, event_file, request):
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
            event_name=request.param,  # 'check_run'
            event_path=str(event_file),  # '/github/workflow/event.json'
            workspace='/github/workspace',
            sha='e6d4abcb8a6cd989d41ee',
            ref='refs/heads/master',
            token='8sdfn12lifds8sdvh832n32f9jew',
        ),
        server=WebServerConfig(),
        runtime=RuntimeConfig(),
    )


@pytest.mark.parametrize(
    'config, event_file, expected_return_code',
    (
        ('check_run', 'created', 1),
        ('unmatched_event', 'closed', 0),
        ('neutral_event', 'qwerty', 78),
    ),
    indirect=('config', 'event_file'),
)
def test_action_processing_return_code(config, expected_return_code):
    """Test an empty action processing run."""
    with pytest.raises(
            SystemExit,
            match=r'^'
            f'{expected_return_code}'
            r'$',
    ):
        run(config=config)
