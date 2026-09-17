"""Test for asynchronous operations utility functions."""

import logging

import anyio

import pytest

from octomachinery.utils.asynctools import (
    aio_gather, amap, dict_to_kwargs_cb, try_await,
)


def sync_power2(val):
    """Raise x to the power of 2."""
    return val ** 2


async def async_power2(val):
    """Raise x to the power of 2 asynchronously."""
    return sync_power2(val)


@pytest.mark.parametrize(
    'callback_func',
    (
        sync_power2,
        async_power2,
    ),
)
@pytest.mark.anyio
async def test_amap(callback_func):
    """Test that async map works for both sync and async callables."""
    async def async_iter(*args, **kwargs):
        for _ in range(*args, **kwargs):
            yield _

    test_range = 5

    actual_result = [
        i async for i in amap(callback_func, async_iter(test_range))
    ]
    expected_result = [
        await try_await(callback_func(i)) for i in range(test_range)
    ]
    assert actual_result == expected_result


@pytest.mark.parametrize(
    'callback_func',
    (
        sync_power2,
        async_power2,
    ),
)
@pytest.mark.anyio
async def test_dict_to_kwargs_cb(callback_func):
    """Test that input dict is turned into given (a)sync callable args."""
    test_val = 5
    test_dict = {'val': test_val}

    actual_result = await dict_to_kwargs_cb(callback_func)(test_dict)
    expected_result = await try_await(callback_func(test_val))
    assert actual_result == expected_result


@pytest.mark.parametrize(
    'callback_func,callback_arg',
    (
        (sync_power2, 3),
        (async_power2, 8),
    ),
)
@pytest.mark.anyio
async def test_try_await(callback_func, callback_arg):
    """Test that result is awaited regardless of (a)sync func type."""
    actual_result = await try_await(callback_func(callback_arg))
    expected_result = callback_arg ** 2
    assert actual_result == expected_result


@pytest.mark.anyio
async def test_try_await_bypass_errors():
    """Test that internal callback exceptions are propagated."""
    async def break_callback():
        raise TypeError('It is broken')

    with pytest.raises(TypeError, match='It is broken'):
        await try_await(break_callback())


@pytest.mark.anyio
async def test_aio_gather_keeps_order():
    """Test that results are returned in the order of the passed tasks."""
    async def sleep_then_return(delay, val):
        await anyio.sleep(delay)
        return val

    actual_result = await aio_gather(
        sleep_then_return(0.02, 'slow'),
        sleep_then_return(0, 'fast'),
        async_power2(3),
    )
    assert actual_result == ('slow', 'fast', 9)


@pytest.mark.anyio
async def test_aio_gather_no_tasks():
    """Test that gathering nothing returns an empty tuple."""
    assert await aio_gather() == ()


@pytest.mark.anyio
async def test_aio_gather_reraises_unwrapped_and_cancels_the_rest():
    """Test that a task failure is propagated as is.

    It must not be wrapped into an exception group so that the callers
    are able to catch it by type. The remaining tasks must be cancelled.
    """
    was_cancelled = anyio.Event()

    async def break_callback():
        raise LookupError('It is broken')

    async def wait_forever():
        try:
            await anyio.sleep(float('inf'))
        except anyio.get_cancelled_exc_class():
            was_cancelled.set()
            raise

    with pytest.raises(LookupError, match='It is broken'):
        await aio_gather(wait_forever(), break_callback())

    assert was_cancelled.is_set()


@pytest.mark.anyio
async def test_aio_gather_logs_the_leftover_failures(caplog):
    """Test that the failures that aren't re-raised are logged."""
    async def break_callback(exc_msg):
        raise LookupError(exc_msg)

    with caplog.at_level(logging.ERROR), pytest.raises(LookupError):
        await aio_gather(
            break_callback('The first one'),
            break_callback('The second one'),
        )

    logged_excs = [
        str(log_rec.exc_info[1]) for log_rec in caplog.records
        if log_rec.exc_info is not None
    ]
    assert logged_excs == ['The second one']
