"""Generic GitHub event containers."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Mapping, TextIO, TYPE_CHECKING, Union
import uuid
import warnings

import attr
from gidgethub.sansio import Event as _GidgetHubEvent

# pylint: disable=relative-beyond-top-level
from ...utils.asynctools import aio_gather
# pylint: disable=relative-beyond-top-level
from ..utils.event_utils import (
    augment_http_headers,
    parse_event_stub_from_fd,
    validate_http_headers,
)

if TYPE_CHECKING:
    # pylint: disable=relative-beyond-top-level
    from ...app.routing.abc import OctomachineryRouterBase


__all__ = 'GitHubEvent', 'GitHubWebhookEvent'


def _to_uuid4(value: Union[str, uuid.UUID]) -> uuid.UUID:
    """Return a UUID from the value."""
    if isinstance(value, uuid.UUID):
        return value

    return uuid.UUID(value, version=4)


def _to_dict(value: Union[dict, bytes, str]) -> dict:
    """Return a dict from the value."""
    if isinstance(value, dict):
        return value

    if isinstance(value, bytes):
        value = value.decode()

    return json.loads(value)


@attr.dataclass(frozen=True)
class GitHubEvent:
    """Representation of a generic source-agnostic GitHub event."""

    name: str
    """Event name."""
    payload: dict = attr.ib(converter=_to_dict)
    """Event payload object."""

    # pylint: disable=no-self-use
    @payload.validator
    def _is_payload_dict(self, attribute: str, value: dict) -> None:
        """Verify that the attribute value is a dict.

        :raises ValueError: if it's not
        """
        if isinstance(value, dict):
            return

        raise ValueError(
            f'{value!r} is passed as {attribute!s} but it must '
            'be an instance of dict',
        )

    @classmethod
    def from_file(
            cls: GitHubEvent,
            event_name: str,
            event_path: Union[pathlib.Path, str],
    ) -> GitHubEvent:
        """Construct a GitHubEvent instance from event name and file."""
        # NOTE: This could be async but it probably doesn't matter
        # NOTE: since it's called just once during init and GitHub
        # NOTE: Action runtime only has one event to process
        # NOTE: OTOH it may slow-down tests parallelism
        # NOTE: so may deserve to be fixed
        with pathlib.Path(event_path).open() as event_source:
            return cls(event_name, json.load(event_source))

    @classmethod
    def from_fixture_fd(
            cls: GitHubEvent,
            event_fixture_fd: TextIO,
            *,
            event: str = None,
    ) -> GitHubEvent:
        """Make a GitHubEvent from a fixture fd and an optional name."""
        headers, payload = parse_event_stub_from_fd(event_fixture_fd)
        if event and 'x-github-event' in headers:
            raise ValueError(
                'Supply only one of an event name '
                'or an event header in the fixture file',
            )
        event_name = event or headers['x-github-event']
        return cls(event_name, payload)

    @classmethod
    def from_fixture(
            cls: GitHubEvent,
            event_fixture_path: Union[pathlib.Path, str],
            *,
            event: str = None,
    ) -> GitHubEvent:
        """Make a GitHubEvent from a fixture and an optional name."""
        with pathlib.Path(event_fixture_path).open() as event_source:
            return cls.from_fixture_fd(event_source, event=event)

    @classmethod
    def from_gidgethub(cls, event: _GidgetHubEvent) -> GitHubEvent:
        """Construct GitHubEvent from from GidgetHub Event."""
        return cls(
            name=event.event,
            payload=event.data,
        )

    def to_gidgethub(self) -> _GidgetHubEvent:
        """Produce GidgetHub Event from self."""
        return _GidgetHubEvent(
            data=self.payload,
            event=self.name,
            delivery_id=str(uuid.uuid4()),
        )

    # pylint: disable=no-self-use
    async def dispatch_via(
            self,
            *routers: OctomachineryRouterBase,
            ctx: Mapping[str, Any] = None,
    ) -> None:
        """Invoke this event handlers from different routers."""
        if not routers:
            raise ValueError('At least one router must be supplied')

        if ctx is None:
            ctx = {}

        await aio_gather(*(
            r.dispatch(self, **ctx)
            for r in routers
        ))


@attr.dataclass(frozen=True)
class GitHubWebhookEvent(GitHubEvent):
    """Representation of a GitHub event arriving by HTTP."""

    delivery_id: uuid.UUID = attr.ib(converter=_to_uuid4)
    """A unique UUID4 identifier of the event delivery on GH side."""

    # pylint: disable=no-self-use
    @delivery_id.validator
    def _is_delivery_id(self, attribute: str, value: uuid.UUID) -> None:
        """Verify that the attribute value is UUID v4.

        :raises ValueError: if it's not
        """
        if isinstance(value, uuid.UUID) and value.version == 4:
            return

        raise ValueError(
            f'{value!r} is passed as {attribute!s} but it must '
            'be an instance of UUID v4',
        )

    @classmethod
    def from_file(
            cls: GitHubWebhookEvent,
            event_name: str,
            event_path: Union[pathlib.Path, str],
    ) -> GitHubWebhookEvent:
        """Explode when constructing from file."""
        raise RuntimeError(
            'Webhook event is not supposed to be constructed from a file',
        )

    @classmethod
    def from_fixture_fd(
            cls: GitHubWebhookEvent,
            event_fixture_fd: TextIO,
            *,
            event: str = None,
    ) -> GitHubWebhookEvent:
        """Make GitHubWebhookEvent from fixture fd and optional name."""
        headers, payload = parse_event_stub_from_fd(event_fixture_fd)
        if event and 'x-github-event' in headers:
            raise ValueError(
                'Supply only one of an event name '
                'or an event header in the fixture file',
            )
        headers['x-github-event'] = event or headers['x-github-event']
        headers = augment_http_headers(headers)
        validate_http_headers(headers)

        return cls(
            name=headers['x-github-event'],
            payload=payload,
            delivery_id=headers['x-github-delivery'],
        )

    @classmethod
    def from_fixture(
            cls: GitHubWebhookEvent,
            event_fixture_path: Union[pathlib.Path, str],
            *,
            event: str = None,
    ) -> GitHubWebhookEvent:
        """Make a GitHubWebhookEvent from fixture and optional name."""
        with pathlib.Path(event_fixture_path).open() as event_source:
            return cls.from_fixture_fd(event_source, event=event)

    @classmethod
    def from_http_request(
            cls: GitHubWebhookEvent,
            http_req_headers: Mapping[str, str],
            http_req_body: bytes,
    ):
        """Make a GitHubWebhookEvent from HTTP req headers and body."""
        return cls(
            name=http_req_headers['x-github-event'],
            payload=json.loads(http_req_body.decode()),
            delivery_id=http_req_headers['x-github-delivery'],
        )

    @classmethod
    def from_gidgethub(cls, event: _GidgetHubEvent) -> GitHubWebhookEvent:
        """Construct GitHubWebhookEvent from from GidgetHub Event."""
        return cls(
            name=event.event,
            payload=event.data,
            delivery_id=event.delivery_id,
        )

    def to_gidgethub(self) -> _GidgetHubEvent:
        """Produce GidgetHub Event from self."""
        return _GidgetHubEvent(
            data=self.payload,
            event=self.name,  # pylint: disable=no-member
            delivery_id=self.delivery_id,
        )


class GidgetHubEventMixin:
    """A temporary shim for GidgetHub event interfaces.

    It's designed to be used during the refactoring period when interfacing
    with the new event representation layer :py:class:`~GitHubEvent`.
    """

    @property
    def data(self):
        """Event payload dict alias."""
        warnings.warn(
            "Relying on GidgetHub's event class interfaces will be deprecated "
            "in the future releases. Please use 'payload' attribute to access "
            'the event name instead.',
            category=PendingDeprecationWarning,
            stacklevel=2,
        )
        return self.payload

    @property
    def event(self):
        """Event name alias."""
        warnings.warn(
            "Relying on GidgetHub's event class interfaces will be deprecated "
            "in the future releases. Please use 'name' attribute to access "
            'the event name instead.',
            category=PendingDeprecationWarning,
            stacklevel=2,
        )
        return self.name


class GidgetHubActionEvent(GidgetHubEventMixin, GitHubEvent):
    """GitHub Action event wrapper exposing GidgetHub attrs."""


class GidgetHubWebhookEvent(GidgetHubEventMixin, GitHubWebhookEvent):
    """GitHub HTTP event wrapper exposing GidgetHub attrs."""
