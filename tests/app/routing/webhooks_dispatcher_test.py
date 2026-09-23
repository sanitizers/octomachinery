"""Test the HTTP request handling in front of the webhook dispatcher."""

from http import HTTPStatus

from aiohttp import web
from aiohttp.test_utils import make_mocked_request

import pytest

from octomachinery.app.routing.webhooks_dispatcher import (
    route_github_webhook_event,
)


@pytest.mark.anyio
async def test_ping_healthcheck():
    """Test that ``GET /ping`` gets a ``PONG`` without a GitHub App."""
    # pylint: disable=missing-kwoa,too-many-function-args
    response = await route_github_webhook_event(
        make_mocked_request('GET', '/ping'),
        github_app=None,
    )

    assert response.status == HTTPStatus.OK
    assert response.text == 'PONG'


@pytest.mark.anyio
@pytest.mark.parametrize(
    ('http_method', 'url_path', 'expected_exception'),
    (
        ('GET', '/', web.HTTPMethodNotAllowed),
        ('POST', '/ping', web.HTTPForbidden),
    ),
)
async def test_non_healthcheck_request(
        http_method, url_path, expected_exception,
):
    """Test that other requests still go through the webhook checks.

    An unsigned ``POST /ping`` is rejected by the signature check,
    meaning that it's handled as a webhook event delivery.
    """
    with pytest.raises(expected_exception):
        # pylint: disable=missing-kwoa,too-many-function-args
        await route_github_webhook_event(
            make_mocked_request(http_method, url_path),
            github_app=None,
            webhook_secret='webhook-secret',
        )
