"""GitHub webhooks routing."""

from functools import wraps

from gidgethub.routing import Router


__all__ = ('dispatch_event', 'process_event', 'process_event_actions')


WEBHOOK_EVENTS_ROUTER = Router()
"""An event dispatcher for webhooks."""


dispatch_event = WEBHOOK_EVENTS_ROUTER.dispatch  # pylint: disable=invalid-name
process_event = WEBHOOK_EVENTS_ROUTER.register  # pylint: disable=invalid-name


def process_event_actions(event_name, actions):
    """Subscribe to multiple events."""
    def decorator(original_function):
        def wrapper(*args, **kwargs):
            return original_function(*args, **kwargs)
        for action in actions:
            wrapper = process_event(event_name, action=action)(wrapper)
        return wraps(original_function)(wrapper)
    return decorator
