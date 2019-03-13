"""A collection of utility functions helping with models."""

from datetime import datetime, timezone
from functools import singledispatch
import sys


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


class SecretStr(str):
    """String that censors its __repr__ if called from another repr."""

    def __repr__(self):
        """Produce a string representation."""
        frame_depth = 1

        try:
            while True:
                frame = sys._getframe(  # pylint: disable=protected-access
                    frame_depth,
                )
                frame_depth += 1

                if frame.f_code.co_name == '__repr__':
                    return '<SECRET>'
        except ValueError:
            pass

        return super().__repr__()


class SuperSecretStr(SecretStr):
    """String that always censors its __repr__."""

    def __repr__(self):
        """Produce a string representation."""
        return '<SUPER_SECRET>'
