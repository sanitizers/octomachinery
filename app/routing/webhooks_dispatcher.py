"""GitHub webhook events dispatching logic."""

import asyncio
from http import HTTPStatus
import logging

from aiohttp import web
from gidgethub import BadRequest, ValidationFailure

# pylint: disable=relative-beyond-top-level
from ..runtime.context import RUNTIME_CONTEXT
from . import dispatch_event


__all__ = ('route_github_webhook_event', )


logger = logging.getLogger(__name__)


EVENT_LOG_TMPL = (
    'Got a{}valid X-GitHub-Event=%s '
    'with X-GitHub-Delivery=%s '
    'and X-Hub-Signature=%s'
)

EVENT_INVALID_CHUNK = 'n in'
EVENT_VALID_CHUNK = ' '

EVENT_LOG_VALID_MSG = EVENT_LOG_TMPL.format(EVENT_VALID_CHUNK)
EVENT_LOG_INVALID_MSG = EVENT_LOG_TMPL.format(EVENT_INVALID_CHUNK)


async def route_github_webhook_event(request):
    """Dispatch incoming webhook events to corresponsing handlers."""
    github_app = RUNTIME_CONTEXT.github_app

    if RUNTIME_CONTEXT.config.runtime.debug:
        logger.debug(
            'Running a GitHub App under env=%s',
            RUNTIME_CONTEXT.config.runtime.env,
        )

    if request.method != 'POST':
        raise web.HTTPMethodNotAllowed(
            method=request.method,
            allowed_methods=('POST'),
        ) from BadRequest(HTTPStatus.METHOD_NOT_ALLOWED)

    webhook_event_signature = request.headers.get(
        'X-Hub-Signature', '<MISSING>',
    )
    try:
        event = await RUNTIME_CONTEXT.github_app.event_from_request(request)
    except ValidationFailure as no_signature_exc:
        logger.info(
            EVENT_LOG_INVALID_MSG,
            request.headers.get('X-GitHub-Event'),
            request.headers.get('X-GitHub-Delivery'),
            webhook_event_signature,
        )
        raise web.HTTPForbidden from no_signature_exc
    else:
        logger.info(
            EVENT_LOG_VALID_MSG,
            event.event,
            event.delivery_id,
            webhook_event_signature,
        )

    app_installation = await github_app.get_installation(event)
    RUNTIME_CONTEXT.app_installation = (  # pylint: disable=assigning-non-slot
        app_installation
    )

    await asyncio.sleep(1)  # Give GitHub a sec to deal w/ eventual consistency
    async with github_app.github_client:
        await dispatch_event(event)
    return web.Response(
        text=f'OK: GitHub event received. It is {event.event!s} ({event!r})',
    )
