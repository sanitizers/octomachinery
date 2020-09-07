# FIXME: is this even needed?
from __future__ import annotations

import logging
from typing import Iterable, Optional, TYPE_CHECKING

from aiohttp.web_runner import GracefulExit
from anyio import run as run_until_complete
import attr

# pylint: disable=relative-beyond-top-level
from ..app.server.machinery import run_forever

# pylint: disable=relative-beyond-top-level
from ..app.config import BotAppConfig

# pylint: disable=relative-beyond-top-level
from ..routing.default_router import WEBHOOK_EVENTS_ROUTER

# pylint: disable=relative-beyond-top-level
from ..utils.asynctools import auto_cleanup_aio_tasks

if TYPE_CHECKING:
    # pylint: disable=relative-beyond-top-level
    from ..routing.abc import OctomachineryRouterBase


logger = logging.getLogger(__name__)


# server entity vs client-holding object?
@attr.s
class GitHubApplication:  # server-only?
# GitHubEventsReceiver?
# GitHubAppsContainer?
# OctomachineryApplication?
    _event_routers: Iterable[OctomachineryRouterBase] = attr.ib(
        default={WEBHOOK_EVENTS_ROUTER},
        converter=frozenset,
    )
    _config: Optional[BotAppConfig] = attr.ib(
        default=None,
    )

    @auto_cleanup_aio_tasks
    async def serve_forever(self):
        """Spawn an HTTP server in an async context."""
        return await run_forever(self._config, self._event_routers)
    accept_webhooks = serve_forever

    @classmethod
    def run_simple(  # FIXME:
            cls,
            *,
            name: Optional[str] = None,
            version: Optional[str] = None,
            url: Optional[str] = None,
            config: Optional[BotAppConfig] = None,
            event_routers: Optional[Iterable[OctomachineryRouterBase]] = None,
    ):
        """Start up a server."""
        if (
                config is not None and
                (name is not None or version is not None or url is not None)
        ):
            raise TypeError(
                f'{cls.__name__}.run_simple() takes name, '
                'version and url arguments only if '
                'the config is not provided.',
            )
        if config is None:
            config = BotAppConfig.from_dotenv(
                app_name=name,
                app_version=version,
                app_url=url,
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

        cls_kwargs = {'config': config}
        if event_routers is not None:
            cls_kwargs['event_routers'] = event_routers

        cls(**cls_kwargs).start()

    def start(self):
        try:
            run_until_complete(self.serve_forever)
        except (GracefulExit, KeyboardInterrupt):
            logger.info(' Exiting the app '.center(50, '='))

    block = start

    #@classmethod
    #run??serve_forever w/ anyio? like app.server.runner

    #also need an instance method too
