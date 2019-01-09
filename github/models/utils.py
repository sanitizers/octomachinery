"""A collection of utility functions helping with models."""

from datetime import datetime, timezone
from functools import singledispatch


@singledispatch
def convert_datetime(datetime_obj) -> datetime:
    """Convert arbitrary object into a datetime instance."""
    raise ValueError(
        f'The input arg type {type(datetime_obj)} is not supported',
    )


@convert_datetime.register
def _(date_unixtime: int) -> datetime:
    return datetime.fromtimestamp(date_unixtime, timezone.utc)


@convert_datetime.register
def _(date_string: str) -> datetime:
    date_string = date_string.replace('.000Z', '.000000Z')
    if '.' not in date_string:
        date_string = date_string.replace('Z', '.000000Z')
    if '+' not in date_string:
        date_string += '+00:00'

    # datetime.fromisoformat() doesn't understand microseconds
    return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ%z')
