"""Ping event handler."""
print(f'{__file__} imported')
import logging

from octomachinery.app.routing import process_event
from octomachinery.app.routing import WEBHOOK_EVENTS_ROUTER
from octomachinery.app.routing.decorators import process_webhook_payload
from octomachinery.app.runtime.context import RUNTIME_CONTEXT


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@process_event('ping')
@process_webhook_payload
async def on_ping(*, hook, hook_id, zen):
    """React to ping webhook event."""
    print('got ping')
    app_id = hook['app_id']

    logger.info(
        'Processing ping for App ID %s '
        'with Hook ID %s '
        'sharing Zen: %s',
        app_id,
        hook_id,
        zen,
    )

    logger.info(
        'Github App Wrapper from context in ping handler: %s',
        RUNTIME_CONTEXT.github_app,
    )
