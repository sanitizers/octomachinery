"""Webhook event processing helper decorators."""

from functools import wraps


def process_webhook_payload(wrapped_function):
    """Bypass event object keys-values as args to the handler."""
    @wraps(wrapped_function)
    def wrapper(event):
        return wrapped_function(**event.data)
    return wrapper
