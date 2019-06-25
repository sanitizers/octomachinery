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
        config: Optional[BotAppConfig] = None,
):
    """Start up a server using CLI args for host and port."""
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
    RUNTIME_CONTEXT.config = config  # pylint: disable=assigning-non-slot

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
        asyncio.run(run_server_forever(config))
    except KeyboardInterrupt:
        logger.info(' Exiting the app '.center(50, '='))
