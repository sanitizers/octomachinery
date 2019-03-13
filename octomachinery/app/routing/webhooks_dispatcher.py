"""GitHub webhook events dispatching logic."""

import asyncio
from functools import wraps
from http import HTTPStatus
import logging

from aiohttp import web
from gidgethub import BadRequest, ValidationFailure

# pylint: disable=relative-beyond-top-level,import-error
from ..runtime.context import RUNTIME_CONTEXT
from . import dispatch_event


__all__ = ('route_github_action_event', 'route_github_webhook_event', )


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


async def get_event_from_request(request):
    """Retrieve Event out of HTTP request if it's valid."""
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
        return event


def validate_allowed_http_methods(*allowed_methods):
    """Block disallowed HTTP methods."""
    if not allowed_methods:
        allowed_methods = {'POST'}
    else:
        allowed_methods = set(allowed_methods)

    def decorator(wrapped_function):
        @wraps(wrapped_function)
        async def wrapper(request):
            if request.method not in allowed_methods:
                raise web.HTTPMethodNotAllowed(
                    method=request.method,
                    allowed_methods=allowed_methods,
                ) from BadRequest(HTTPStatus.METHOD_NOT_ALLOWED)
            return await wrapped_function(request)
        return wrapper
    return decorator


@validate_allowed_http_methods('POST')
async def route_github_webhook_event(request):
    """Dispatch incoming webhook events to corresponsing handlers."""
    github_app = RUNTIME_CONTEXT.github_app

    event = await get_event_from_request(request)

    await asyncio.sleep(1)  # Give GitHub a sec to deal w/ eventual consistency
    async with github_app.github_app_client:
        github_installation = await github_app.get_installation(event)
        github_installation_client = (
            github_installation.github_installation_client
        )
        async with github_installation_client as gh_install_client:
            # pylint: disable=assigning-non-slot
            RUNTIME_CONTEXT.app_installation_client = gh_install_client
            await dispatch_event(event)
    return web.Response(
        text=f'OK: GitHub event received. It is {event.event!s} ({event!r})',
    )


async def route_github_action_event(github_action):
    """Dispatch a GitHub action event to corresponsing handlers."""
    async with github_action.github_installation_client as gh_install_client:
        # pylint: disable=assigning-non-slot
        RUNTIME_CONTEXT.app_installation_client = gh_install_client
        await dispatch_event(github_action.event)
