"""Test app server machinery."""
# pylint: disable=redefined-outer-name

import uuid

from aiohttp.client import ClientSession
import pytest

from octomachinery.app.config import BotAppConfig
from octomachinery.app.server.machinery import start_site
from octomachinery.github.api.app_client import GitHubApp


@pytest.fixture
def github_app_id() -> int:
    """Return a GitHub App ID."""
    return 0


@pytest.fixture
def octomachinery_config(
        github_app_id: int, rsa_private_key_bytes: bytes,
) -> None:
    """Initialize a GitHub App bot config."""
    # https://github.com/hynek/environ-config/blob/master/CHANGELOG.rst#1910-2019-09-02
    return BotAppConfig.from_environ({  # pylint: disable=no-member
        'GITHUB_APP_IDENTIFIER': str(github_app_id),
        'GITHUB_PRIVATE_KEY': rsa_private_key_bytes.decode(),
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
def github_app(octomachinery_config_github_app, aiohttp_client_session):
    """Initizalize a GitHub App instance."""
    return GitHubApp(octomachinery_config_github_app, aiohttp_client_session)


@pytest.fixture
async def octomachinery_app(github_app, octomachinery_config_server):
    """Run octomachinery web server and tear-down after testing."""
    tcp_site = await start_site(octomachinery_config_server, github_app)
    try:
        yield
    finally:
        await tcp_site.stop()


@pytest.fixture
async def send_webhook_event(
        octomachinery_app,  # pylint: disable=unused-argument
        octomachinery_config_server,
        github_app,  # pylint: disable=unused-argument
        aiohttp_client_session,
):
    """Return a webhook sender coroutine."""
    def _send_event(webhook_payload=None):
        post_body = {} if webhook_payload is None else webhook_payload

        webhook_endpoint_url = (
            f'http://{octomachinery_config_server.host}'
            f':{octomachinery_config_server.port}/'
        )
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
        'OK: GitHub event received. '
        'It is ping (<gidgethub.sansio.Event object at '
    )

    assert resp_content_type == 'text/plain; charset=utf-8'
    assert resp_body.startswith(expected_response_start)
