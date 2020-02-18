"""GitHub webhook events dispatching logic."""

from __future__ import annotations

import contextlib
import logging

from anyio import sleep as async_sleep

# pylint: disable=relative-beyond-top-level,import-error
from ..runtime.context import RUNTIME_CONTEXT
# pylint: disable=relative-beyond-top-level,import-error
from ..github.entities.action import GitHubAction


__all__ = ('route_github_event', )


logger = logging.getLogger(__name__)


async def route_github_event(*, github_event, github_app):
    """Dispatch GitHub event to corresponsing handlers.

    Set up ``RUNTIME_CONTEXT`` before doing that. This is so
    the concrete event handlers have access to the API client
    and flags in runtime.
    """
    is_gh_action = isinstance(github_app, GitHubAction)
    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.IS_GITHUB_ACTION = is_gh_action
    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.IS_GITHUB_APP = not is_gh_action

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.github_app = github_app

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.github_event = github_event

    # pylint: disable=assigning-non-slot
    RUNTIME_CONTEXT.app_installation = None
    if is_gh_action:
        # pylint: disable=assigning-non-slot
        RUNTIME_CONTEXT.app_installation_client = github_app.api_client
    else:
        with contextlib.suppress(LookupError):
            # pylint: disable=pointless-string-statement
            """Provision an installation API client if possible.

            Some events (like `ping`) are
            happening application/GitHub-wide and are not bound to
            a specific installation. The webhook payloads of such events
            don't contain any reference to an installaion.
            Some events don't even refer to a GitHub App
            (e.g. `security_advisory`).
            """
            github_install = await github_app.get_installation(github_event)
            # pylint: disable=assigning-non-slot
            RUNTIME_CONTEXT.app_installation = github_install
            # pylint: disable=assigning-non-slot
            RUNTIME_CONTEXT.app_installation_client = github_install.api_client

        # Give GitHub a sec to deal w/ eventual consistency.
        # This is only needed for events that arrive over HTTP.
        # If the dispatcher is invoked from GitHub Actions,
        # by the time it's invoked the action must be already consistently
        # distributed within GitHub's systems because spawning VMs takes time
        # and actions are executed in workflows that rely on those VMs.
        await async_sleep(1)

    return await github_app.dispatch_event(github_event)
