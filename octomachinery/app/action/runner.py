"""Octomachinery CLI runner for GitHub Action environments."""

import asyncio
import logging
from typing import Iterable, Optional

from aiohttp.client import ClientSession

# pylint: disable=relative-beyond-top-level
from ...github.entities.action import GitHubAction
# pylint: disable=relative-beyond-top-level
from ...github.errors import GitHubActionError
# pylint: disable=relative-beyond-top-level
from ...github.models.action_outcomes import (
    ActionSuccess, ActionNeutral, ActionFailure,
)
# pylint: disable=relative-beyond-top-level
from ..config import BotAppConfig
# pylint: disable=relative-beyond-top-level
from ..routing import WEBHOOK_EVENTS_ROUTER
# pylint: disable=relative-beyond-top-level
from ..routing.abc import OctomachineryRouterBase
# pylint: disable=relative-beyond-top-level
from ..routing.webhooks_dispatcher import route_github_event


logger = logging.getLogger(__name__)


async def process_github_action(config, event_routers):
    """Schedule GitHub Action event for processing."""
    logger.info('Processing GitHub Action event...')

    async with ClientSession() as http_client_session:
        github_action = GitHubAction(
            metadata=config.action,
            http_session=http_client_session,
            config=config.github,
            event_routers=event_routers,
        )
        logger.info('GitHub Action=%r', config.action)

        await route_github_event(
            github_event=github_action.event,
            github_app=github_action,
        )
    return ActionSuccess('GitHub Action has been processed')


def run(
        *,
        config: Optional[BotAppConfig] = None,
        event_routers: Optional[Iterable[OctomachineryRouterBase]] = None,
) -> None:
    """Start up a server using CLI args for host and port."""
    if event_routers is None:
        event_routers = {WEBHOOK_EVENTS_ROUTER}

    if config is None:
        config = BotAppConfig.from_dotenv()

    logging.basicConfig(
        level=logging.DEBUG
        if config.runtime.debug  # pylint: disable=no-member
        else logging.INFO,
    )

    try:
        processing_outcome = asyncio.run(
            process_github_action(config, event_routers),
        )
    except GitHubActionError as action_error:
        action_error.terminate_action()
    except KeyboardInterrupt:
        ActionNeutral('Action processing interrupted by user').raise_it()
    except Exception:  # pylint: disable=broad-except
        err_msg = 'Action processing failed unexpectedly'
        logger.exception(err_msg)
        ActionFailure(err_msg).raise_it()
    else:
        processing_outcome.raise_it()
