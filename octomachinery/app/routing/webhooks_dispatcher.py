"""GitHub webhook events dispatching logic."""

import asyncio
import contextlib
from functools import wraps
from http import HTTPStatus
import logging
import typing

from aiohttp import web
from anyio import sleep as async_sleep
from gidgethub import BadRequest, ValidationFailure

# pylint: disable=relative-beyond-top-level,import-error
from ...github.models.events import GidgetHubWebhookEvent
# pylint: disable=relative-beyond-top-level,import-error
from ..runtime.context import RUNTIME_CONTEXT
from . import WEBHOOK_EVENTS_ROUTER


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
        http_req_body = await github_app.trusted_payload_from_request(request)
    except ValidationFailure as no_signature_exc:
        logger.error(
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
        event = GidgetHubWebhookEvent.from_http_request(
            http_req_headers=request.headers,
            http_req_body=http_req_body,
        )
        logger.info(
            EVENT_LOG_VALID_MSG,
            event.name,  # pylint: disable=no-member
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


def webhook_request_to_event(wrapped_function):
    """Pass event extracted from request into the wrapped function."""
    @wraps(wrapped_function)
    async def wrapper(request, *, github_app):
        event = await get_event_from_request(request, github_app)
        return await wrapped_function(
            github_event=event, github_app=github_app,
        )
    return wrapper


@validate_allowed_http_methods('POST')
@webhook_request_to_event
async def route_github_webhook_event(*, github_event, github_app):
    """Dispatch incoming webhook events to corresponsing handlers."""
    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.IS_GITHUB_ACTION = False
    RUNTIME_CONTEXT.IS_GITHUB_APP = True  # pylint: disable=assigning-non-slot

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.github_app = github_app

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.github_event = github_event

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
        github_install = await github_app.get_installation(github_event)
        # pylint: disable=assigning-non-slot
        RUNTIME_CONTEXT.app_installation = github_install
        # pylint: disable=assigning-non-slot
        RUNTIME_CONTEXT.app_installation_client = github_install.api_client

    await async_sleep(1)  # Give GitHub a sec to deal w/ eventual consistency
    asyncio.create_task(github_event.dispatch_via(WEBHOOK_EVENTS_ROUTER))
    event_ack_msg = f'GitHub event received. It is {github_event!r}'
    return web.Response(text=f'OK: {event_ack_msg}')


# pylint: disable=unused-argument
async def route_github_action_event(github_action, *, github_app=None):
    """Dispatch a GitHub action event to corresponsing handlers."""
    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.IS_GITHUB_ACTION = True
    RUNTIME_CONTEXT.IS_GITHUB_APP = False  # pylint: disable=assigning-non-slot
    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.github_event = github_action.event

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.app_installation_client = github_action.api_client
    await github_action.event.dispatch_via(WEBHOOK_EVENTS_ROUTER)
