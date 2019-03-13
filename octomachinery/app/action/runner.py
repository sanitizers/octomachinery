"""Octomachinery CLI runner for GitHub Action environments."""

import asyncio
import logging

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
from ..routing.webhooks_dispatcher import (
    route_github_action_event,
)
# pylint: disable=relative-beyond-top-level
from ..runtime.context import RUNTIME_CONTEXT


logger = logging.getLogger(__name__)


async def process_github_action(config):
    """Schedule GitHub Action event for processing."""
    logger.info('Processing GitHub Action event...')

    github_action = GitHubAction(config.action)
    logger.info('GitHub Action=%r', config.action)

    await route_github_action_event(github_action)
    return ActionSuccess('GitHub Action has been processed')


def run():
    """Start up a server using CLI args for host and port."""
    config = BotAppConfig.from_dotenv()
    RUNTIME_CONTEXT.config = config  # pylint: disable=assigning-non-slot
    logging.basicConfig(
        level=logging.DEBUG
        if config.runtime.debug  # pylint: disable=no-member
        else logging.INFO,
    )
    try:
        processing_outcome = asyncio.run(process_github_action(config))
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
