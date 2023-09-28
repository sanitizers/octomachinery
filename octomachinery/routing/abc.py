"""Octomachinery router base interface definitions."""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Iterator

from gidgethub.routing import AsyncCallback


if TYPE_CHECKING:
    from ..github.models.events import GitHubEvent


__all__ = ('OctomachineryRouterBase',)


class OctomachineryRouterBase(metaclass=ABCMeta):
    """Octomachinery router base."""

    # pylint: disable=unused-argument
    @abstractmethod
    def emit_routes_for(
            self, event_name: str, event_payload: Any,
    ) -> Iterator[AsyncCallback]:
        """Emit callbacks that match given event and payload.

        :param str event_name: name of the GitHub event
        :param str event_payload: details of the GitHub event

        :yields: coroutine event handlers
        """

    # pylint: disable=unused-argument
    @abstractmethod
    async def dispatch(
            self, event: 'GitHubEvent',
            *args: Any, **kwargs: Any,
    ) -> None:
        """Invoke coroutine handler tasks for the given event."""
