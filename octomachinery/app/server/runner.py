"""Octomachinery CLI runner."""

import asyncio
import logging
import sys
from typing import Optional

import attr

# pylint: disable=relative-beyond-top-level
from ..config import BotAppConfig
# pylint: disable=relative-beyond-top-level
from ..runtime.context import RUNTIME_CONTEXT
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
):
    """Start up a server using CLI args for host and port."""
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
    RUNTIME_CONTEXT.config = config  # pylint: disable=assigning-non-slot
    if config.runtime.debug:  # pylint: disable=no-member
        logging.basicConfig(level=logging.DEBUG)

        logger.debug(
            ' App version: %s '.center(50, '='),
            config.runtime.app_version,
        )
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(run_server_forever(config))
    except KeyboardInterrupt:
        logger.info(' Exiting the app '.center(50, '='))
