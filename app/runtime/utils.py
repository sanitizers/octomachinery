"""GitHub App runtime context helpers."""

import os

from contextvars import ContextVar


class ContextLookupError(AttributeError):
    """Context var lookup error."""


class _ContextMap:
    __slots__ = '__map__', '__token_map__'

    def __init__(self, **initial_vars):
        self.__map__ = {k: ContextVar(v) for k, v in initial_vars.items()}
        """Storage for all context vars."""

        self.__token_map__ = {}
        """Storage for individual context var reset tokens."""

    def __getattr__(self, name):
        if name in ('__map__', '__token_map__'):
            return getattr(self, name)
        try:
            return self.__map__[name].get()
        except LookupError:
            raise ContextLookupError(f'No `{name}` present in the context')

    def __setattr__(self, name, value):
        if name in ('__map__', '__token_map__'):
            object.__setattr__(self, name, value)
        elif name in self.__map__:
            reset_token = self.__map__[name].set(value)
            self.__token_map__[name] = reset_token
        else:
            raise ContextLookupError(f'No `{name}` present in the context')

    def __delattr__(self, name):
        if name not in self.__map__:
            raise ContextLookupError(f'No `{name}` present in the context')
        reset_token = self.__token_map__[name]
        self.__map__[name].reset(reset_token)
        del self.__token_map__[name]


def detect_env_mode():
    """Figure out whether we're under GitHub Action environment."""
    for var_suffix in {
            'WORKFLOW',
            'ACTION', 'ACTOR',
            'REPOSITORY',
            'EVENT_NAME', 'EVENT_PATH',
            'WORKSPACE',
            'SHA', 'REF',
            'TOKEN',
    }:
        if f'GITHUB_{var_suffix}' not in os.environ:
            return 'app'
    return 'action'
