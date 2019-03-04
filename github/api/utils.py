"""Utilitary helpers."""

from functools import wraps


def mark_uninitialized_in_repr(cls):
    """Patch __repr__ for uninitialized instances."""
    orig_repr = cls.__repr__

    @wraps(orig_repr)
    def new_repr(self):
        if not self.is_initialized:
            return f'{self.__class__.__name__}(<UNINITIALIZED>)'
        return orig_repr(self)
    cls.__repr__ = new_repr
    return cls
