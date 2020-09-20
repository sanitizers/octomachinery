"""GitHub webhook events dispatching logic."""

from __future__ import annotations

import contextlib
import logging

from anyio import get_cancelled_exc_class, sleep as async_sleep
import sentry_sdk

# pylint: disable=relative-beyond-top-level,import-error
from ..runtime.context import RUNTIME_CONTEXT
# pylint: disable=relative-beyond-top-level,import-error
from ..github.api.app_client import GitHubApp
# pylint: disable=relative-beyond-top-level,import-error
from ..github.entities.action import GitHubAction
# pylint: disable=relative-beyond-top-level,import-error
from ..github.errors import GitHubActionError
# pylint: disable=relative-beyond-top-level,import-error
from ..github.models.events import GitHubEvent


__all__ = ('route_github_event', )


logger = logging.getLogger(__name__)


async def route_github_event(
        *,
        github_event: GitHubEvent,
        github_app: GitHubApp,
) -> None:
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

    try:
        return await github_app.dispatch_event(github_event)
    except GitHubActionError:
        # Bypass GitHub Actions errors as they are supposed to be a
        # mechanism for communicating outcomes and are expected.
        raise
    except get_cancelled_exc_class():
        raise
    except Exception as exc:  # pylint: disable=broad-except
        # NOTE: It's probably better to wrap each event handler with
        # NOTE: try/except and call `capture_exception()` there instead.
        # NOTE: We'll also need to figure out the magic of associating
        # NOTE: breadcrumbs with event handlers.
        sentry_sdk.capture_exception(exc)

        # NOTE: Framework-wise, these exceptions are meaningless because they
        # NOTE: can be anything random that the webhook author (octomachinery
        # NOTE: end-user) forgot to handle. There's nothing we can do about
        # NOTE: them except put in the log so that the end-user would be able
        # NOTE: to properly debug their problem by inspecting the logs.
        # NOTE: P.S. This is also where we'd inject Sentry
        if isinstance(exc.__context__, get_cancelled_exc_class()):
            # The CancelledError context is irrelevant to the
            # user-defined webhook event handler workflow so we're
            # dropping it from the logs:
            exc.__context__ = None

        logger.exception(
            'An unhandled exception happened while running webhook '
            'event handlers for "%s"...',
            github_event.name,
        )
        delivery_id_msg = (
            '' if is_gh_action
            else f' (Delivery ID: {github_event.delivery_id!s})'
        )
        logger.debug(
            'The payload of "%s" event%s is: %r',
            github_event.name, delivery_id_msg, github_event.payload,
        )

        if is_gh_action:
            # NOTE: In GitHub Actions env, the app is supposed to run as
            # NOTE: a foreground single event process rather than a
            # NOTE: server for multiple events. It's okay to propagate
            # NOTE: unhandled errors so that they are spit out to the
            # NOTE: console.
            raise
    except BaseException:  # SystemExit + KeyboardInterrupt + GeneratorExit
        raise
