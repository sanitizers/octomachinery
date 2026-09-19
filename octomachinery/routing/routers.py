"""Octomachinery event dispatchers collection."""

import asyncio
from typing import Any, Iterator, Set, Union

from gidgethub.routing import AsyncCallback
from gidgethub.routing import Router as _GidgetHubRouter

from ..github.models.events import (
    GidgetHubWebhookEvent, GitHubEvent, _GidgetHubEvent,
)
from ..utils.asynctools import aio_gather
from .abc import OctomachineryRouterBase


__all__ = (
    'GidgetHubRouterBase',
    'ConcurrentRouter',
    'NonBlockingConcurrentRouter',
)


class GidgetHubRouterBase(_GidgetHubRouter, OctomachineryRouterBase):
    """GidgetHub-based router exposing callback matching separately."""

    def emit_routes_for(
            self, event_name: str, event_payload: Any,
    ) -> Iterator[AsyncCallback]:
        """Emit callbacks that match given event and payload.

        Callbacks registered for the catch-all ``*`` event name match
        any event and are emitted after the event-specific ones.

        :param str event_name: name of the GitHub event
        :param str event_payload: details of the GitHub event

        :yields: coroutine event handlers
        """
        for route_name in dict.fromkeys((event_name, '*')):
            yield from self._shallow_routes.get(route_name, ())

            deep_routes = self._deep_routes.get(route_name, {})
            for payload_key, payload_values in deep_routes.items():
                if payload_key not in event_payload:
                    continue
                event_value = event_payload[payload_key]
                if event_value not in payload_values:
                    continue
                yield from payload_values[event_value]

    async def dispatch(
            self, event: Union[GidgetHubWebhookEvent, _GidgetHubEvent],
            *args: Any, **kwargs: Any,
    ) -> None:
        """Invoke handler tasks for the given event sequentially."""
        if isinstance(event, _GidgetHubEvent):
            event = GidgetHubWebhookEvent.from_gidgethub(event)

        callback_gen = self.emit_routes_for(event.name, event.payload)
        callback_coros = (cb(event, *args, **kwargs) for cb in callback_gen)

        for coro in callback_coros:
            await coro


class ConcurrentRouter(GidgetHubRouterBase):
    """GitHub event router invoking event handlers simultaneously."""

    async def dispatch(
            self, event: GitHubEvent,
            *args: Any, **kwargs: Any,
    ) -> None:
        """Invoke coroutine callbacks for the given event together."""
        callback_gen = self.emit_routes_for(event.name, event.payload)
        callback_coros = (cb(event, *args, **kwargs) for cb in callback_gen)

        await aio_gather(*callback_coros)


class NonBlockingConcurrentRouter(ConcurrentRouter):
    """Non-blocking GitHub event router scheduling handler tasks."""

    def __init__(self, *args, **kwargs):
        """Initialize NonBlockingConcurrentRouter."""
        super().__init__(*args, **kwargs)
        # NOTE: For some reason, mypy doesn't accept anything except Any here:
        self._event_handler_tasks: Set[Any] = set()

    async def dispatch(
            self, event: GitHubEvent,
            *args: Any, **kwargs: Any,
    ) -> None:
        """Schedule coroutine callbacks for the given event together."""
        callback_gen = self.emit_routes_for(event.name, event.payload)
        callback_coros = (cb(event, *args, **kwargs) for cb in callback_gen)
        handler_tasks = map(asyncio.create_task, callback_coros)
        self._event_handler_tasks.update(handler_tasks)
