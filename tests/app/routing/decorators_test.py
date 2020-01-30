"""Test event routing decorator helpers."""

import pytest

from octomachinery.app.routing.decorators import process_webhook_payload
from octomachinery.github.models.events import GitHubEvent


@process_webhook_payload
def fake_event_handler(*, arg1, arg2):
    """Process fake test event."""
    return arg1, arg2


@pytest.mark.parametrize(
    'incoming_event,is_successful',
    (
        ({'arg1': 'y', 'arg2': 'x'}, True),
        ({'arg0': 'p', 'arg1': 'u', 'arg2': 'n'}, False),
        ({'arg1': 'z'}, False),
        ({'arg3': 's'}, False),
        (dict(), False),
    ),
)
def test_process_webhook_payload(incoming_event, is_successful):
    """Test that @process_webhook_payload unpacks event into kw-args."""
    event = GitHubEvent(name=None, payload=incoming_event)

    if is_successful:
        assert (
            # pylint: disable=missing-kwoa,too-many-function-args
            fake_event_handler(event)
            == tuple(incoming_event.values())
        )
    else:
        with pytest.raises(TypeError):
            # pylint: disable=missing-kwoa,too-many-function-args
            fake_event_handler(event)
