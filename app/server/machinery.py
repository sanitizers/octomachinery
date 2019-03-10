"""Web-server constructors."""

import asyncio
import logging

from aiohttp import web

# pylint: disable=relative-beyond-top-level
from ...github.api.app_client import GitHubApp
# pylint: disable=relative-beyond-top-level
from ..routing.webhooks_dispatcher import (
    route_github_webhook_event,
)
# pylint: disable=relative-beyond-top-level
from ..runtime.context import RUNTIME_CONTEXT


logger = logging.getLogger(__name__)


async def start_tcp_site(server_config, aiohttp_server_runner):
    """Return initialized and listening TCP site."""
    host, port = server_config.host, server_config.port
    aiohttp_tcp_site = web.TCPSite(aiohttp_server_runner, host, port)
    await aiohttp_tcp_site.start()
    logger.info(
        f' Serving on http://%s:%s/ '.center(50, '='),
        host, port,
    )
    return aiohttp_tcp_site


async def get_server_runner(http_handler):
    """Initialize server runner."""
    aiohttp_server = web.Server(http_handler)
    aiohttp_server_runner = web.ServerRunner(aiohttp_server)
    await aiohttp_server_runner.setup()
    return aiohttp_server_runner


async def run_forever(config):
    """Spawn an HTTP server in asyncio context."""
    async with GitHubApp(config.github) as github_app:
        logger.info('Starting the following GitHub App:')
        logger.info(
            '* app id: %s',
            github_app._config.app_id,  # pylint: disable=protected-access
        )
        logger.info(
            '* user agent: %s',
            github_app._config.user_agent,  # pylint: disable=protected-access
        )
        RUNTIME_CONTEXT.github_app = (  # pylint: disable=assigning-non-slot
            github_app
        )
        aiohttp_server_runner = await get_server_runner(
            route_github_webhook_event,
        )
        aiohttp_tcp_site = await start_tcp_site(
            config.server, aiohttp_server_runner,
        )

        if RUNTIME_CONTEXT.config.runtime.debug:
            logger.debug(
                'Running a GitHub App under env=%s',
                RUNTIME_CONTEXT.config.runtime.env,
            )

        try:
            await asyncio.get_event_loop().create_future()  # block
        except asyncio.CancelledError:
            logger.info(' Stopping the server '.center(50, '='))
            await aiohttp_tcp_site.stop()
