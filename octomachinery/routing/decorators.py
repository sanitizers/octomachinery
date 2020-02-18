"""Webhook event processing helper decorators."""

from __future__ import annotations

from functools import wraps
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    # pylint: disable=relative-beyond-top-level
    from ..github.models.events import GitHubEvent


__all__ = ('process_webhook_payload', )


def process_webhook_payload(wrapped_function):
    """Bypass event object keys-values as args to the handler."""
    @wraps(wrapped_function)
    def wrapper(event: GitHubEvent) -> Any:
        return wrapped_function(**event.payload)
    return wrapper
