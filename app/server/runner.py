"""Octomachinery CLI runner."""

import asyncio
import logging
import sys

import attr

# pylint: disable=relative-beyond-top-level
from ...app.config import BotAppConfig
# pylint: disable=relative-beyond-top-level
from ...app.runtime.context import RUNTIME_CONTEXT
# pylint: disable=relative-beyond-top-level
from .config import WebServerConfig
# pylint: disable=relative-beyond-top-level
from .machinery import run_forever as run_server_forever


logger = logging.getLogger(__name__)


def run():
    """Start up a server using CLI args for host and port."""
    config = BotAppConfig.from_dotenv()
    if len(sys.argv) > 2:
        config = attr.evolve(
            config,
            server=WebServerConfig(*sys.argv[1:3]),
        )
    RUNTIME_CONTEXT.config = config  # pylint: disable=assigning-non-slot
    if config.runtime.debug:  # pylint: disable=no-member
        logging.basicConfig(level=logging.DEBUG)

        from octomachinery.github.config.utils import APP_VERSION
        logger.debug(
            ' App version: %s '.center(50, '='),
            APP_VERSION,
        )
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(run_server_forever(config))
    except KeyboardInterrupt:
        logger.info(' Exiting the app '.center(50, '='))
