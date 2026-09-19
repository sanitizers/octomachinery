"""Asynchronous tools set."""

from functools import wraps
from inspect import isawaitable as _is_awaitable
from inspect import signature as _inspect_signature
from logging import getLogger as _get_logger
from operator import itemgetter
from typing import Any, Optional, Tuple

from anyio import EndOfStream, WouldBlock, create_memory_object_stream
from anyio import create_task_group as all_subtasks_awaited
from anyio import get_cancelled_exc_class as _get_cancelled_exc_class
from anyio.streams.memory import (
    MemoryObjectReceiveStream, MemoryObjectSendStream,
)


logger = _get_logger(__name__)

_TaskOutcome = Tuple[int, Any, Optional[Exception]]


def auto_cleanup_aio_tasks(async_func):
    """Ensure all subtasks finish."""
    @wraps(async_func)
    async def async_func_wrapper(*args, **kwargs):
        async with all_subtasks_awaited():
            return await async_func(*args, **kwargs)
    return async_func_wrapper


async def _send_task_res_to_q(res_q, task_id, aio_task):
    """Await task and send its result or exception to the stream."""
    try:
        task_res = await aio_task
    except _get_cancelled_exc_class():
        # NOTE: Under Python 3.7, `CancelledError` is a subclass of
        # NOTE: `Exception` so it has to be let through explicitly,
        # NOTE: or a cancelled sibling would report it as an outcome.
        raise
    except Exception as exc:  # pylint: disable=broad-except
        res_q.send_nowait((task_id, None, exc))
    else:
        res_q.send_nowait((task_id, task_res, None))


def _log_leftover_task_failures(res_q):
    """Log the task failures that won't be re-raised."""
    while True:
        try:
            _task_id, _task_res, task_exc = res_q.receive_nowait()
        except (EndOfStream, WouldBlock):
            return

        if task_exc is not None:
            # NOTE: `logger.exception()` that G201 suggests implies
            # NOTE: `exc_info=True`, which reads the exception being
            # NOTE: currently handled. These ones are detached from
            # NOTE: their handlers, so they have to be passed in
            # NOTE: explicitly:
            logger.error(  # noqa: G201
                'Another gathered task failed', exc_info=task_exc,
            )


async def _aio_gather_iter_pairs(*aio_tasks):
    """Spawn async tasks and yield with pairs of ids with results.

    The first task failure cancels the rest of the tasks. It is then
    re-raised as is. Raising it from within the task group would get
    it wrapped into an exception group under anyio 4+, making it
    impossible to catch by its own type.
    """
    aio_tasks_num = len(aio_tasks)
    task_res_send_q: MemoryObjectSendStream[_TaskOutcome]
    task_res_recv_q: MemoryObjectReceiveStream[_TaskOutcome]
    task_res_send_q, task_res_recv_q = create_memory_object_stream(
        aio_tasks_num,
    )
    task_exc = None

    # NOTE: The streams must outlive the task group so that the
    # NOTE: children could still report their outcomes while it is
    # NOTE: unwinding. This is why they are entered first.
    async with task_res_send_q, task_res_recv_q:
        async with all_subtasks_awaited() as task_group:
            for task_id, task in enumerate(aio_tasks):
                task_group.start_soon(
                    _send_task_res_to_q,
                    task_res_send_q,
                    task_id, task,
                )

            for _ in range(aio_tasks_num):
                task_id, task_res, task_exc = await task_res_recv_q.receive()
                if task_exc is not None:
                    task_group.cancel_scope.cancel()
                    break
                yield task_id, task_res

        if task_exc is not None:
            _log_leftover_task_failures(task_res_recv_q)

    if task_exc is not None:
        raise task_exc


async def aio_gather_iter(*aio_tasks):
    """Spawn async tasks and yield results.

    The iterator must be consumed to exhaustion. Abandoning it early
    leaves the underlying task group to be closed by the async
    generator finalizer, which runs in a different task, making anyio
    reject the cancel scope exit.
    """
    async for _task_id, task_res in _aio_gather_iter_pairs(*aio_tasks):
        yield task_res


async def aio_gather(*aio_tasks):
    """Spawn async tasks and return results in the same order."""
    result_pairs_gen = [_r async for _r in _aio_gather_iter_pairs(*aio_tasks)]
    sorted_result_pairs = sorted(result_pairs_gen, key=itemgetter(0))
    all_task_results = map(itemgetter(1), sorted_result_pairs)
    return tuple(all_task_results)


async def try_await(potentially_awaitable):
    """Try awaiting the arg and return it regardless."""
    if _is_awaitable(potentially_awaitable):
        return await potentially_awaitable

    return potentially_awaitable


async def amap(callback, async_iterable):
    """Map asynchronous generator with a coroutine or a function."""
    async for async_value in async_iterable:
        yield await try_await(callback(async_value))


def dict_to_kwargs_cb(callback):
    """Return a callback mapping dict to keyword arguments."""
    cb_arg_names = set(_inspect_signature(callback).parameters.keys())

    async def callback_wrapper(args_dict):
        excessive_arg_names = set(args_dict.keys()) - cb_arg_names
        filtered_args_dict = {
            arg_name: arg_value for arg_name, arg_value in args_dict.items()
            if arg_name not in excessive_arg_names
        } if excessive_arg_names else args_dict
        if excessive_arg_names:
            logger.warning(
                'Excessive arguments passed to callback %(callable)s',
                {'callable': callback},
                extra={
                    'callable': callback,
                    'excessive-arg-names': excessive_arg_names,
                    'passed-in-args': args_dict,
                    'forwarded-args': filtered_args_dict,
                },
            )
        return await try_await(callback(**filtered_args_dict))
    return callback_wrapper
