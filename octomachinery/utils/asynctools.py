"""Asynchronous tools set."""


async def try_await(potentially_awaitable):
    """Try awaiting the arg and return it regardless."""
    valid_exc_str = (
        "can't be used in 'await' expression"
    )

    try:
        return await potentially_awaitable
    except TypeError as type_err:
        type_err_msg = str(type_err)
        if not (
                type_err_msg.startswith('object ')
                and type_err_msg.endswith(valid_exc_str)
        ):
            raise

    return potentially_awaitable


async def amap(callback, async_iterable):
    """Map asyncronous generator with a coroutine or a function."""
    async for async_value in async_iterable:
        yield await try_await(callback(async_value))


def dict_to_kwargs_cb(callback):
    """Return a callback mapping dict to keyword arguments."""
    async def callback_wrapper(args_dict):
        return await try_await(callback(**args_dict))
    return callback_wrapper
