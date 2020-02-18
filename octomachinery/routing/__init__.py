"""GitHub webhooks routing."""


# pylint: disable=unused-import
from .default_router import (  # noqa: F401
    dispatch_event,
    process_event,
    process_event_actions,
    WEBHOOK_EVENTS_ROUTER,
)
