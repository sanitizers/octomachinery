"""Test for asynchronous operations utility functions."""

import pytest

from octomachinery.utils.asynctools import amap, dict_to_kwargs_cb, try_await


def sync_power2(val):
    """Raise x to the power of 2."""
    return val ** 2


async def async_power2(val):
    """Raise x to the power of 2 asyncronously."""
    return sync_power2(val)


@pytest.mark.parametrize(
    'callback_func',
    (
        sync_power2,
        async_power2,
    ),
)
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
async def test_try_await(callback_func, callback_arg):
    """Test that result is awaited regardless of (a)sync func type."""
    actual_result = await try_await(callback_func(callback_arg))
    expected_result = callback_arg ** 2
    assert actual_result == expected_result


async def test_try_await_bypass_errors():
    """Test that internal callback exceptions are propagated."""
    async def break_callback():
        raise TypeError('It is broken')

    with pytest.raises(TypeError, match='It is broken'):
        await try_await(break_callback())
