"""Test GitHub event routers."""

import pytest

from octomachinery.routing.routers import ConcurrentRouter


# pylint: disable=unused-argument
async def on_issues(event):
    """Handle any ``issues`` event."""


async def on_opened_issue(event):
    """Handle an ``issues`` event with the ``opened`` action."""


async def on_any_event(event):
    """Handle any event."""


async def on_anything_opened(event):
    """Handle any event with the ``opened`` action."""


@pytest.fixture
def events_router():
    """Construct a router with event-specific and catch-all routes."""
    router = ConcurrentRouter()
    router.add(on_issues, 'issues')
    router.add(on_opened_issue, 'issues', action='opened')
    router.add(on_any_event, '*')
    router.add(on_anything_opened, '*', action='opened')
    return router


@pytest.mark.parametrize(
    ('event_name', 'event_payload', 'expected_callbacks'),
    (
        pytest.param(
            'issues', {'action': 'opened'},
            [on_issues, on_opened_issue, on_any_event, on_anything_opened],
            id='specific-and-catch-all-deep-match',
        ),
        pytest.param(
            'issues', {'action': 'closed'},
            [on_issues, on_any_event],
            id='specific-and-catch-all-shallow-match',
        ),
        pytest.param(
            'pull_request', {'action': 'opened'},
            [on_any_event, on_anything_opened],
            id='catch-all-only-deep-match',
        ),
        pytest.param(
            'ping', {'zen': 'Keep it logically awesome.'},
            [on_any_event],
            id='catch-all-only-shallow-match',
        ),
    ),
)
def test_emit_routes_for(
        events_router, event_name, event_payload, expected_callbacks,
):
    """Test that catch-all routes are emitted after event-specific ones."""
    emitted_callbacks = events_router.emit_routes_for(
        event_name, event_payload,
    )
    assert list(emitted_callbacks) == expected_callbacks


def test_emit_routes_for_unrouted_event():
    """Test that a router without matching routes emits nothing."""
    router = ConcurrentRouter()
    router.add(on_issues, 'issues')
    assert not list(router.emit_routes_for('ping', {}))
