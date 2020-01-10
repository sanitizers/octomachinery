"""GitHub webhook events dispatching logic."""

import asyncio
import contextlib
from functools import wraps
from http import HTTPStatus
import logging
import typing

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


async def get_event_from_request(request, github_app):
    """Retrieve Event out of HTTP request if it's valid."""
    webhook_event_signature = request.headers.get(
        'X-Hub-Signature', '<MISSING>',
    )
    try:
        event = await github_app.event_from_request(request)
    except ValidationFailure as no_signature_exc:
        logger.info(
            EVENT_LOG_INVALID_MSG,
            request.headers.get('X-GitHub-Event'),
            request.headers.get('X-GitHub-Delivery'),
            webhook_event_signature,
        )
        logger.debug(
            'Webhook HTTP query signature validation failed because: %s',
            no_signature_exc,
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


def validate_allowed_http_methods(*allowed_methods: str):
    """Block disallowed HTTP methods."""
    _allowed_methods: typing.Set[str]
    if not allowed_methods:
        _allowed_methods = {'POST'}
    else:
        _allowed_methods = set(allowed_methods)

    def decorator(wrapped_function):
        @wraps(wrapped_function)
        async def wrapper(request, *, github_app):
            if request.method not in _allowed_methods:
                raise web.HTTPMethodNotAllowed(
                    method=request.method,
                    allowed_methods=_allowed_methods,
                ) from BadRequest(HTTPStatus.METHOD_NOT_ALLOWED)
            return await wrapped_function(request, github_app=github_app)
        return wrapper
    return decorator


@validate_allowed_http_methods('POST')
async def route_github_webhook_event(request, *, github_app):
    """Dispatch incoming webhook events to corresponsing handlers."""
    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.IS_GITHUB_ACTION = False
    RUNTIME_CONTEXT.IS_GITHUB_APP = True  # pylint: disable=assigning-non-slot

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.github_app = github_app

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.github_event = event = (
        await get_event_from_request(request, github_app)
    )

    with contextlib.suppress(LookupError):
        # pylint: disable=pointless-string-statement
        """Provision an installation API client if possible.

        Some events (like `ping`) are
        happening application/GitHub-wide and are not bound to
        a specific installation. The webhook payloads of such events
        don't contain any reference to an installaion.
        Some events don't even refer to a GitHub App
        (e.g. `security_advisory`).
        """
        github_install = await github_app.get_installation(event)
        # pylint: disable=assigning-non-slot
        RUNTIME_CONTEXT.app_installation = github_install
        # pylint: disable=assigning-non-slot
        RUNTIME_CONTEXT.app_installation_client = github_install.api_client

    await asyncio.sleep(1)  # Give GitHub a sec to deal w/ eventual consistency
    await dispatch_event(event)
    return web.Response(
        text=f'OK: GitHub event received. It is {event.event!s} ({event!r})',
    )


async def route_github_action_event(github_action):
    """Dispatch a GitHub action event to corresponsing handlers."""
    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.IS_GITHUB_ACTION = True
    RUNTIME_CONTEXT.IS_GITHUB_APP = False  # pylint: disable=assigning-non-slot
    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.github_event = github_action.event

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.app_installation_client = github_action.api_client
    await dispatch_event(github_action.event)
