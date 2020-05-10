"""Web-server constructors."""

import functools
import logging

import anyio
from aiohttp.client import ClientSession
from aiohttp import web

# pylint: disable=relative-beyond-top-level
from ...github.api.app_client import GitHubApp
# pylint: disable=relative-beyond-top-level
from ...utils.asynctools import auto_cleanup_aio_tasks
# pylint: disable=relative-beyond-top-level
from ..routing.webhooks_dispatcher import route_github_webhook_event


logger = logging.getLogger(__name__)


async def start_tcp_site(
        server_config, aiohttp_server_runner: web.ServerRunner,
) -> web.TCPSite:
    """Return initialized and listening TCP site."""
    host, port = server_config.host, server_config.port
    aiohttp_tcp_site = web.TCPSite(aiohttp_server_runner, host, port)
    await aiohttp_tcp_site.start()
    logger.info(
        ' Serving on %s '.center(50, '='),
        aiohttp_tcp_site.name,
    )
    return aiohttp_tcp_site


async def get_server_runner(http_handler):
    """Initialize server runner."""
    aiohttp_server = web.Server(http_handler)
    aiohttp_server_runner = web.ServerRunner(
        aiohttp_server,
        # handle SIGTERM and SIGINT
        # by raising aiohttp.web_runner.GracefulExit exception
        handle_signals=True,
    )
    await aiohttp_server_runner.setup()
    return aiohttp_server_runner


async def _prepare_github_app(github_app):
    """Set GitHub App in the context."""
    logger.info('Starting the following GitHub App:')
    logger.info(
        '* app id: %s',
        github_app._config.app_id,  # pylint: disable=protected-access
    )
    logger.info(
        '* private key SHA-1 fingerprint: %s',
        # pylint: disable=protected-access
        github_app._config.private_key.fingerprint,
    )
    logger.info(
        '* user agent: %s',
        github_app._config.user_agent,  # pylint: disable=protected-access
    )
    await github_app.log_installs_list()


async def _launch_web_server_and_wait_until_it_stops(
        web_server_config,
        github_app: GitHubApp,
        webhook_secret: str = None,
) -> None:
    """Start a web server.

    And then block until SIGINT comes in.
    """
    aiohttp_server_runner = await setup_server_runner(
        github_app, webhook_secret,
    )
    aiohttp_tcp_site = await start_tcp_site(
        web_server_config, aiohttp_server_runner,
    )
    await _stop_site_on_cancel(aiohttp_tcp_site)


async def setup_server_runner(
        github_app: GitHubApp,
        webhook_secret: str = None,
) -> web.ServerRunner:
    """Return a server runner with a webhook dispatcher set up."""
    return await get_server_runner(
        functools.partial(
            route_github_webhook_event,
            github_app=github_app,
            webhook_secret=webhook_secret,
        ),
    )


async def _stop_site_on_cancel(aiohttp_tcp_site):
    """Stop the server after SIGINT."""
    try:
        await anyio.sleep(float('inf'))
    except anyio.get_cancelled_exc_class():
        logger.info(' Stopping the server '.center(50, '='))
        await aiohttp_tcp_site.stop()


def log_webhook_secret_status(webhook_secret):
    """Log HTTP body signature verification behavior."""
    webhook_secret_repr = (
        f' ({webhook_secret[:1]}...{webhook_secret[-1:]})'
        if webhook_secret else ''
    )
    logger.info(
        'Webhook secret%s is [%sSET]: %s',
        webhook_secret_repr,
        '' if webhook_secret else 'NOT ',
        'SIGNATURE VERIFICATION WILL BE ENFORCED'
        if webhook_secret else 'SIGNED WEBHOOKS WILL BE REJECTED',
    )


@auto_cleanup_aio_tasks
async def run_forever(config, event_routers):
    """Spawn an HTTP server in anyio context."""
    logger.debug('The GitHub App env is set to `%s`', config.runtime.env)
    log_webhook_secret_status(config.github.webhook_secret)
    async with ClientSession() as aiohttp_client_session:
        github_app = GitHubApp(
            config.github,
            http_session=aiohttp_client_session,
            event_routers=event_routers,
        )
        await _prepare_github_app(github_app)
        await _launch_web_server_and_wait_until_it_stops(
            config.server, github_app, config.github.webhook_secret,
        )
