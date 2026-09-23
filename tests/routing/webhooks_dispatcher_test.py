"""Tests for the GitHub event dispatcher."""

import uuid

from aiohttp.client_exceptions import ServerDisconnectedError

import pytest

from octomachinery.github.models.events import GitHubWebhookEvent
from octomachinery.routing.webhooks_dispatcher import route_github_event


class FakeGitHubApp:
    """A GitHub App stub with a configurable installation lookup."""

    def __init__(self, installation_error):
        """Remember the error to raise when looking up an installation."""
        self.installation_error = installation_error
        self.dispatched_events = []

    async def get_installation(self, event):
        """Fail the installation lookup."""
        raise self.installation_error

    async def dispatch_event(self, event):
        """Record the dispatched event."""
        self.dispatched_events.append(event)
        return ()


@pytest.fixture
def github_event():
    """Return a webhook event bound to an installation."""
    return GitHubWebhookEvent(
        name='issues',
        payload={'installation': {'id': 1}},
        delivery_id=uuid.uuid4(),
    )


@pytest.fixture(autouse=True)
def _no_consistency_delay(monkeypatch):
    """Skip waiting for GitHub's eventual consistency."""
    async def no_sleep(seconds):  # pylint: disable=unused-argument
        """Return immediately."""
    monkeypatch.setattr(
        'octomachinery.routing.webhooks_dispatcher.async_sleep', no_sleep,
    )


@pytest.mark.anyio
async def test_installation_lookup_error_logged(github_event, caplog):
    """Test that a failed installation lookup doesn't escape the task."""
    github_app = FakeGitHubApp(ServerDisconnectedError())

    await route_github_event(github_event=github_event, github_app=github_app)

    assert not github_app.dispatched_events
    assert 'An unhandled exception happened' in caplog.text
    assert 'ServerDisconnectedError' in caplog.text


@pytest.mark.anyio
async def test_event_without_installation_dispatched(github_event):
    """Test that events outside of installations are still dispatched."""
    github_app = FakeGitHubApp(LookupError())

    await route_github_event(github_event=github_event, github_app=github_app)

    assert github_app.dispatched_events == [github_event]
