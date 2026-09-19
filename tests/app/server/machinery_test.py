"""Test app server machinery."""

import uuid
from typing import Tuple

from aiohttp.client import ClientSession
from aiohttp.test_utils import get_unused_port_socket
from aiohttp.web import SockSite
from aiohttp.web_runner import GracefulExit

import pytest

from octomachinery.app.config import BotAppConfig
from octomachinery.app.routing import WEBHOOK_EVENTS_ROUTER
from octomachinery.app.server import machinery
from octomachinery.app.server.machinery import run_forever, setup_server_runner
from octomachinery.github.api.app_client import GitHubApp


IPV4_LOCALHOST = '127.0.0.1'


@pytest.fixture
def ephemeral_port_tcp_sock():
    """Initialize an ephemeral TCP socket."""
    tcp_sock = get_unused_port_socket(IPV4_LOCALHOST)
    try:
        yield tcp_sock
    finally:
        # NOTE: The tests that hand the socket over to a server site
        # NOTE: get it closed by that site's clean-up. The ones that
        # NOTE: only need the address it points at would otherwise leak
        # NOTE: it until the garbage collector emits a
        # NOTE: `ResourceWarning`, which `filterwarnings = error` turns
        # NOTE: into a failure of whatever test is running by then.
        tcp_sock.close()


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
        ephemeral_port_tcp_sock_addr: Tuple[str, int],
) -> None:
    """Initialize a GitHub App bot config."""
    host, port = ephemeral_port_tcp_sock_addr
    # https://github.com/hynek/environ-config/blob/master/CHANGELOG.rst#1910-2019-09-02
    # pylint: disable=no-member
    return BotAppConfig.from_environ({  # type: ignore[attr-defined]
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
async def aiohttp_client_session() -> ClientSession:
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
    """Set up an HTTP handler for webhooks and tear it down after."""
    server_runner = await setup_server_runner(github_app)
    try:
        yield server_runner
    finally:
        # NOTE: Since aiohttp v3.9, stopping a site only closes the
        # NOTE: listening socket — shutting down the connections that
        # NOTE: are already established moved into the runner clean-up.
        # NOTE: Without this, the server-side request handler is left
        # NOTE: pending with an open transport that emits a
        # NOTE: `ResourceWarning` whenever it happens to be garbage
        # NOTE: collected, which `filterwarnings = error` turns into a
        # NOTE: failure of whatever unrelated test is running by then.
        await server_runner.cleanup()


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


@pytest.mark.anyio
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


@pytest.mark.parametrize(
    'startup_exc_type',
    (GracefulExit, KeyboardInterrupt, LookupError),
)
@pytest.mark.anyio
async def test_run_forever_propagates_startup_failures_as_is(
        monkeypatch, octomachinery_config, octomachinery_event_routers,
        startup_exc_type,
):
    """Test that a start-up failure reaches the caller unwrapped.

    The CLI runner recognizes the signal-driven shutdown by catching
    :class:`~aiohttp.web_runner.GracefulExit`, so anything that the
    server raises must keep its own type on the way out instead of
    getting wrapped into an exception group.
    """
    async def _fail_to_prepare_github_app(_github_app):
        raise startup_exc_type('Nope')

    monkeypatch.setattr(
        machinery, '_prepare_github_app', _fail_to_prepare_github_app,
    )

    with pytest.raises(startup_exc_type, match='Nope'):
        await run_forever(octomachinery_config, octomachinery_event_routers)
