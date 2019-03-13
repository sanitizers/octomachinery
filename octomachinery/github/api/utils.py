"""Utilitary helpers."""

from functools import wraps
from types import AsyncGeneratorType
from typing import Any, Dict, Tuple

from gidgethub.sansio import accept_format


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


def accept_preview_version(wrapped_coroutine):
    """Extend keyword-args with `preview_api_version`."""
    @wraps(wrapped_coroutine)
    def coroutine_wrapper(
            *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> AsyncGeneratorType:
        accept_media = kwargs.pop('accept', None)
        preview_api_version = kwargs.pop('preview_api_version', None)

        if preview_api_version is not None:
            accept_media = accept_format(
                version=f'{preview_api_version}-preview',
            )
        if accept_media is not None:
            kwargs['accept'] = accept_media

        coroutine_instance = wrapped_coroutine(*args, **kwargs)
        is_async_generator = isinstance(coroutine_instance, AsyncGeneratorType)

        if not is_async_generator:
            async def async_function_wrapper():
                return await coroutine_instance
            return async_function_wrapper()

        async def async_generator_wrapper():
            async for result_item in coroutine_instance:
                yield result_item

        return async_generator_wrapper()

    return coroutine_wrapper
