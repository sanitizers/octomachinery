"""GitHub webhook events dispatching logic."""

import asyncio
from functools import wraps
from http import HTTPStatus
import logging
import typing

from aiohttp import web
from gidgethub import BadRequest, ValidationFailure
from gidgethub.sansio import validate_event as validate_webhook_payload

# pylint: disable=relative-beyond-top-level,import-error
from ...github.models.events import GidgetHubWebhookEvent
# pylint: disable=relative-beyond-top-level,import-error
from ...routing.webhooks_dispatcher import route_github_event


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


async def get_trusted_http_payload(request, webhook_secret):
    """Get a verified HTTP request body from request."""
    http_req_headers = request.headers
    is_secret_provided = webhook_secret is not None
    is_payload_signed = 'x-hub-signature' in http_req_headers

    if is_payload_signed and not is_secret_provided:
        raise ValidationFailure('secret not provided')

    if not is_payload_signed and is_secret_provided:
        raise ValidationFailure('signature is missing')

    raw_http_req_body = await request.read()

    if is_payload_signed and is_secret_provided:
        validate_webhook_payload(
            payload=raw_http_req_body,
            signature=http_req_headers['x-hub-signature'],
            secret=webhook_secret,
        )

    return raw_http_req_body


async def get_event_from_request(request, webhook_secret):
    """Retrieve Event out of HTTP request if it's valid."""
    webhook_event_signature = request.headers.get(
        'X-Hub-Signature', '<MISSING>',
    )
    try:
        http_req_body = await get_trusted_http_payload(
            request, webhook_secret,
        )
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
        async def wrapper(request, *, github_app, webhook_secret=None):
            if request.method not in _allowed_methods:
                raise web.HTTPMethodNotAllowed(
                    method=request.method,
                    allowed_methods=_allowed_methods,
                ) from BadRequest(HTTPStatus.METHOD_NOT_ALLOWED)
            return await wrapped_function(
                request,
                github_app=github_app,
                webhook_secret=webhook_secret,
            )
        return wrapper
    return decorator


def webhook_request_to_event(wrapped_function):
    """Pass event extracted from request into the wrapped function."""
    @wraps(wrapped_function)
    async def wrapper(request, *, github_app, webhook_secret=None):
        event = await get_event_from_request(request, webhook_secret)
        return await wrapped_function(
            github_event=event, github_app=github_app,
        )
    return wrapper


@validate_allowed_http_methods('POST')
@webhook_request_to_event
async def route_github_webhook_event(*, github_event, github_app):
    """Dispatch incoming webhook events to corresponsing handlers."""
    asyncio.create_task(route_github_event(
        github_event=github_event,
        github_app=github_app,
    ))
    event_ack_msg = (
        'GitHub event received and scheduled for processing. '
        f'It is {github_event!r}'
    )
    return web.Response(text=f'OK: {event_ack_msg!s}')
