"""Octomachinery CLI runner."""

import logging
import sys
from typing import Iterable, Optional

from aiohttp.web_runner import GracefulExit
from anyio import run as run_until_complete
import attr

# pylint: disable=relative-beyond-top-level
from ..config import BotAppConfig
# pylint: disable=relative-beyond-top-level
from ..routing import WEBHOOK_EVENTS_ROUTER
# pylint: disable=relative-beyond-top-level
from ..routing.abc import OctomachineryRouterBase
# pylint: disable=relative-beyond-top-level
from .config import WebServerConfig
# pylint: disable=relative-beyond-top-level
from .machinery import run_forever as run_server_forever


logger = logging.getLogger(__name__)


def run(
        *,
        name: Optional[str] = None,
        version: Optional[str] = None,
        url: Optional[str] = None,
        config: Optional[BotAppConfig] = None,
        event_routers: Optional[Iterable[OctomachineryRouterBase]] = None,
):
    """Start up a server using CLI args for host and port."""
    if event_routers is None:
        event_routers = {WEBHOOK_EVENTS_ROUTER}

    if (
            config is not None and
            (name is not None or version is not None or url is not None)
    ):
        raise TypeError(
            'run() takes either a BotAppConfig instance as a config argument '
            'or name, version and url arguments.',
        )
    if config is None:
        config = BotAppConfig.from_dotenv(
            app_name=name,
            app_version=version,
            app_url=url,
        )
        if len(sys.argv) > 2:
            config = attr.evolve(
                config,
                server=WebServerConfig(*sys.argv[1:3]),
            )

    logging.basicConfig(
        level=logging.DEBUG
        if config.runtime.debug  # pylint: disable=no-member
        else logging.INFO,
    )
    if config.runtime.debug:  # pylint: disable=no-member
        logger.debug(
            ' App version: %s '.center(50, '='),
            config.github.app_version,
        )

    try:
        run_until_complete(run_server_forever, config, event_routers)
    except (GracefulExit, KeyboardInterrupt):
        logger.info(' Exiting the app '.center(50, '='))
