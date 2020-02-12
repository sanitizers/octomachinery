"""Test app server machinery."""
# pylint: disable=redefined-outer-name

import uuid

from aiohttp.client import ClientSession
from aiohttp.web import SockSite
from aiohttp.test_utils import get_unused_port_socket
import pytest

from octomachinery.app.config import BotAppConfig
from octomachinery.app.routing import WEBHOOK_EVENTS_ROUTER
from octomachinery.app.server.machinery import setup_server_runner
from octomachinery.github.api.app_client import GitHubApp


IPV4_LOCALHOST = '127.0.0.1'


@pytest.fixture
def ephemeral_port_tcp_sock():
    """Initialize an ephemeral TCP socket."""
    return get_unused_port_socket(IPV4_LOCALHOST)


@pytest.fixture
def ephemeral_port_tcp_sock_addr(ephemeral_port_tcp_sock):
    """Return final host and port addr of the ephemeral TCP socket."""
    return ephemeral_port_tcp_sock.getsockname()[:2]


@pytest.fixture
def github_app_id() -> int:
    """Return a GitHub App ID."""
    return 0


@pytest.fixture
def octomachinery_config(
        github_app_id: int, rsa_private_key_bytes: bytes,
        ephemeral_port_tcp_sock_addr: tuple,
) -> None:
    """Initialize a GitHub App bot config."""
    host, port = ephemeral_port_tcp_sock_addr
    # https://github.com/hynek/environ-config/blob/master/CHANGELOG.rst#1910-2019-09-02
    return BotAppConfig.from_environ({  # pylint: disable=no-member
        'GITHUB_APP_IDENTIFIER': str(github_app_id),
        'GITHUB_PRIVATE_KEY': rsa_private_key_bytes.decode(),
        'HOST': host,
        'PORT': port,
    })


@pytest.fixture
def octomachinery_config_github_app(octomachinery_config):
    """Return a GitHub App bot config section."""
    return octomachinery_config.github


@pytest.fixture
def octomachinery_config_server(octomachinery_config):
    """Return a GitHub App server config section."""
    return octomachinery_config.server


@pytest.fixture
async def aiohttp_client_session(
        loop,  # pylint: disable=unused-argument
) -> ClientSession:
    """Initialize an aiohttp HTTP client session."""
    async with ClientSession() as http_session:
        yield http_session


@pytest.fixture
def octomachinery_event_routers():
    """Construct a set of routers for use in the GitHub App."""
    return frozenset({WEBHOOK_EVENTS_ROUTER})


@pytest.fixture
def github_app(
        octomachinery_config_github_app, aiohttp_client_session,
        octomachinery_event_routers,
):
    """Initizalize a GitHub App instance."""
    return GitHubApp(
        octomachinery_config_github_app,
        aiohttp_client_session,
        octomachinery_event_routers,
    )


@pytest.fixture
async def octomachinery_app_server_runner(github_app):
    """Set up an HTTP handler for webhooks."""
    return await setup_server_runner(github_app)


@pytest.fixture
async def octomachinery_app_tcp(
        ephemeral_port_tcp_sock,
        octomachinery_app_server_runner,
):
    """Run octomachinery web server and tear-down after testing."""
    tcp_site = SockSite(
        octomachinery_app_server_runner, ephemeral_port_tcp_sock,
    )
    await tcp_site.start()
    try:
        yield tcp_site
    finally:
        await tcp_site.stop()


@pytest.fixture
async def send_webhook_event(
        octomachinery_app_tcp, aiohttp_client_session,
):
    """Return a webhook sender coroutine."""
    def _send_event(webhook_payload=None):
        post_body = {} if webhook_payload is None else webhook_payload

        webhook_endpoint_url = octomachinery_app_tcp.name
        return aiohttp_client_session.post(
            webhook_endpoint_url, json=post_body,
            headers={
                'X-GitHub-Delivery': str(uuid.uuid4()),
                'X-GitHub-Event': 'ping',
            },
        )
    return _send_event


async def test_ping_response(send_webhook_event, github_app_id):
    """Test that ping webhook event requests receive a HTTP response."""
    async with send_webhook_event(
            {
                'hook': {'app_id': github_app_id},
                'hook_id': 0,
                'zen': 'Hey zen!',
            },
    ) as gh_app_http_resp:
        resp_body: str = (await gh_app_http_resp.read()).decode()

    resp_content_type = gh_app_http_resp.headers['Content-Type']
    expected_response_start = (
        'OK: GitHub event received and scheduled for processing. '
        "It is GidgetHubWebhookEvent(name='ping', payload={'hook': {"
        f"'app_id': {github_app_id}"
        "}, 'hook_id': 0, 'zen': 'Hey zen!'}, delivery_id=UUID('"
    )

    assert resp_content_type == 'text/plain; charset=utf-8'
    assert resp_body.startswith(expected_response_start)
